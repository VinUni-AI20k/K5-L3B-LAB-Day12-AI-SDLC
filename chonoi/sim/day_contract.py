"""Vòng ngày headless theo Test Contract v1.1."""

import copy
import math

from ..errors import BadInput
from .gather import GatherSim
from .quan import QuanSim


class ContractDaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = copy.deepcopy(tuning)
        self.rng, self.ids = streams, ids
        self.scenario = scenario
        settings = scenario.get("day", {})
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.money = settings.get("money", 0)
        self.earned = settings.get("earned", 0)
        self.reputation = settings.get("reputation", tuning["quan"]["reputation_initial"])
        if (isinstance(self.money, bool) or not isinstance(self.money, int) or self.money < 0
                or isinstance(self.earned, bool) or not isinstance(self.earned, int)
                or self.earned < self.money):
            raise BadInput("day cần 0 <= money <= earned")
        if (isinstance(self.reputation, bool) or not isinstance(self.reputation, (int, float))
                or not math.isfinite(self.reputation)
                or not tuning["quan"]["reputation_min"] <= self.reputation <= tuning["quan"]["reputation_max"]):
            raise BadInput("day.reputation không hợp lệ")
        self.upgrades = {"oxygen": 0, "hp": 0}
        initial_upgrades = settings.get("upgrades", {})
        if not isinstance(initial_upgrades, dict):
            raise BadInput("day.upgrades phải là object")
        self.upgrades.update(initial_upgrades)
        for name, level in self.upgrades.items():
            if name not in ("oxygen", "hp") or isinstance(level, bool) or not isinstance(level, int) or level not in (0, 1, 2):
                raise BadInput("cấp nâng cấp không hợp lệ")
        self.active_upgrades = dict(self.upgrades)
        self.plans = copy.deepcopy(tuning["day_plan"])
        overrides = settings.get("day_plan", [])
        if not isinstance(overrides, list) or not all(isinstance(item, dict) for item in overrides):
            raise BadInput("day.day_plan phải là mảng object")
        seen_days = set()
        for override in overrides:
            number = override.get("day")
            if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= len(self.plans):
                raise BadInput("day_plan có ngày không hợp lệ")
            if number in seen_days:
                raise BadInput("day_plan có ngày trùng")
            seen_days.add(number)
            dishes = override.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day_plan cần dishes")
            ingredients = {}
            for dish, count in dishes.items():
                if dish not in tuning["menu"] or isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                    raise BadInput("món hoặc số suất không hợp lệ")
                for kind, amount in tuning["menu"][dish]["recipe"].items():
                    ingredients[kind] = ingredients.get(kind, 0) + amount * count
            if "ingredients" in override and override["ingredients"] != ingredients:
                raise BadInput("ingredients không khớp công thức")
            self.plans[number - 1] = {"day": number, "dishes": dict(dishes), "ingredients": ingredients}
        self.done = False
        self.reason = None
        self.stock = {}
        self.phase = "gather"
        self.phase_tick = 0
        self._start_gather()

    @property
    def plan(self):
        return self.plans[self.day - 1]

    def _start_gather(self):
        self.phase = "gather"
        self.phase_tick = 0
        self.active_upgrades = dict(self.upgrades)
        tuning = copy.deepcopy(self.tuning)
        for name, level in self.active_upgrades.items():
            if level:
                entry = next(item for item in tuning["shop"]["upgrades"][name] if item["level"] == level)
                field = "oxygen_max_s" if name == "oxygen" else "hp_max"
                tuning["gather"][field] = entry[field]
        self.active = GatherSim(tuning, copy.deepcopy(self.scenario.get("gather", {})), self.rng, self.ids, day=self.day)
        self.time_left_ticks = self.active.time_left_ticks

    def initial_events(self):
        return [("day_start", {}), ("day_plan", {"dishes": self.plan["dishes"],
                                                  "ingredients": self.plan["ingredients"]}), ("phase_start", {})]

    def _start_quan(self):
        self.phase = "quan"
        self.phase_tick = 0
        scenario = copy.deepcopy(self.scenario.get("quan", {}))
        if "stock" in scenario or "reputation" in scenario:
            raise BadInput("day không nhận quan.stock hoặc quan.reputation")
        scenario["reputation"] = self.reputation
        self.active = QuanSim(self.tuning, scenario, self.rng, self.ids, inventory=self.stock,
                              dish_pool=self.plan["dishes"].keys())
        self.active.money, self.active.earned = self.money, self.earned
        self.time_left_ticks = self.active.time_left_ticks

    def _start_shop(self):
        self.phase = "shop"
        self.phase_tick = 0
        self.time_left_ticks = self.tuning["shop"]["max_ticks"]

    def _buy(self, name):
        catalog = self.tuning["shop"]["upgrades"]
        if name not in catalog:
            return ("buy_failed", {"action": name, "reason": "unknown"})
        current = self.upgrades[name]
        choices = [item for item in catalog[name] if item["level"] == current + 1]
        if not choices:
            return ("buy_failed", {"action": name, "reason": "max_level"})
        item = choices[0]
        if self.money < item["price"]:
            return ("buy_failed", {"action": name, "reason": "funds"})
        self.money -= item["price"]
        self.upgrades[name] = item["level"]
        return ("bought", {"upgrade": name, "level": item["level"], "price": item["price"], "money": self.money})

    def step(self, inp):
        self.phase_tick += 1
        if self.phase == "shop":
            self.time_left_ticks = max(0, self.time_left_ticks - 1)
            result = [self._buy(inp.buy)] if inp.buy else []
            if inp.pressed("shop_done") or self.time_left_ticks == 0:
                reason = "done" if inp.pressed("shop_done") else "time"
                result.append(("shop_end", {"reason": reason}))
                self.days_completed += 1
                if self.days_completed >= self.days:
                    self.done, self.reason = True, "days_complete"
                else:
                    self.day += 1
                    self.stock = {}
                    self._start_gather()
                    result.extend(self.initial_events())
            return result
        result = self.active.step(inp)
        self.time_left_ticks = self.active.time_left_ticks
        if self.phase == "quan":
            self.money, self.earned, self.reputation = self.active.money, self.active.earned, self.active.reputation
        if not self.active.done:
            return result
        if self.phase == "gather":
            self.stock = self.active.inventory_items()
            self._start_quan()
        else:
            self.money, self.earned, self.reputation = self.active.money, self.active.earned, self.active.reputation
            self.stock = dict(self.active.stock)
            self._start_shop()
        result.append(("phase_start", {}))
        return result

    def snapshot(self):
        result = {"day": self.day, "day_plan": {"dishes": self.plan["dishes"],
                                                    "ingredients": self.plan["ingredients"]},
                  "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades)}
        if self.phase == "shop":
            result["stock"] = dict(self.stock)
        else:
            result.update(self.active.snapshot())
        return result
