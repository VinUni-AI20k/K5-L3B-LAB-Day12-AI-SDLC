"""Vòng ngày và cửa hàng dùng chung giữa headless và live."""

from collections import Counter
from copy import deepcopy

from .errors import BadInput
from .freshness import ITEM_ID_PREFIX, view_items
from .ids import IdAllocator, sort_by_id
from .rng import Streams


def _positive_int(value):
    return type(value) is int and value > 0


def day_plans(tuning, overrides=()):
    plans = {}
    for entries in (tuning["day_plan"], overrides):
        if not isinstance(entries, (list, tuple)):
            raise BadInput("day_plan phải là mảng")
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) - {"day", "dishes", "ingredients"}:
                raise BadInput("day_plan có mục sai schema")
            number, dishes = entry.get("day"), entry.get("dishes")
            if not _positive_int(number) or number > 5 or number in seen:
                raise BadInput("day_plan.day phải duy nhất trong [1, 5]")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day_plan.dishes phải là object không rỗng")
            ingredients = Counter()
            for dish, servings in dishes.items():
                if dish not in tuning["menu"] or not _positive_int(servings):
                    raise BadInput("day_plan.dishes: món không hợp lệ hoặc số suất sai")
                for kind, amount in tuning["menu"][dish]["recipe"].items():
                    ingredients[kind] += servings * amount
            if "ingredients" in entry:
                given = entry["ingredients"]
                if (not isinstance(given, dict) or not all(_positive_int(n) for n in given.values())
                        or given != ingredients):
                    raise BadInput("day_plan.ingredients khác tổng công thức")
            seen.add(number)
            plans[number] = {"dishes": dict(dishes), "ingredients": dict(ingredients)}
        if set(plans) != {1, 2, 3, 4, 5}:
            raise BadInput("tuning.day_plan phải đủ Ngày 1–5")
    return plans


def gather_tuning(tuning, upgrades):
    gather = dict(tuning["gather"])
    for name, key in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        level = upgrades.get(name, 0)
        if level:
            gather[key] = tuning["shop"]["upgrades"][name][level - 1][key]
    return {**tuning, "gather": gather}


class Shop:
    mode = phase = "shop"

    def __init__(self, tuning, quan, upgrades, freshness=None):
        self.tuning = tuning
        self.upgrades = upgrades
        self.freshness = freshness
        self.stock = [item.copy() for item in quan.stock] if freshness else dict(quan.stock)
        self.money, self.earned, self.reputation = quan.money, quan.earned, quan.reputation
        self.time_left_ticks = tuning["max_ticks"]
        self.done = False
        self.reason = None

    def snapshot(self):
        stock = (view_items(sort_by_id(self.stock), self.freshness["spoiled_below"])
                 if self.freshness else dict(self.stock))
        return {"stock": stock}

    def _buy(self, action):
        offers = self.tuning["upgrades"].get(action)
        level = self.upgrades.get(action, 0)
        if offers is None:
            failure = "unknown"
        elif level >= len(offers):
            failure = "max_level"
        else:
            price = offers[level]["price"]
            if self.money >= price:
                self.money -= price
                self.upgrades[action] = level + 1
                return "bought", {"upgrade": action, "level": level + 1, "price": price, "money": self.money}
            failure = "funds"
        return "buy_failed", {"action": action, "reason": failure}

    def step(self, inp):
        events = []
        self.time_left_ticks -= 1
        if inp.buy is not None:
            events.append(self._buy(inp.buy))
        if inp.pressed("shop_done") or self.time_left_ticks == 0:
            self.done = True
            self.reason = "done" if inp.pressed("shop_done") else "time"
            events.append(("shop_end", {"reason": self.reason}))
        return events


class Day:
    def __init__(self, tuning, scenario, seed, days, gather, quan):
        self.tuning, self.scenario = tuning, scenario
        self.gather, self.quan = gather, quan
        self.streams, self.ids = Streams(seed), IdAllocator()
        initial = scenario.get("day", {})
        self.plans = day_plans(tuning, initial.get("day_plan", ()))
        self.money = initial.get("money", 0)
        self.earned = initial.get("earned", 0)
        self.reputation = initial.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(initial.get("upgrades", {}))
        self.days, self.days_completed = days, 0
        self.number, self.done = 1, False
        self._open_gather()

    def _open_gather(self):
        self.active_upgrades = dict(self.upgrades)
        tuning = gather_tuning(self.tuning, self.active_upgrades)
        scenario = deepcopy(self.scenario.get("gather", {}))
        self.template_item_ids = {}
        if self.number > 1 and "freshness" in tuning:
            for item in scenario.get("hold", []):
                old_id = item["id"]
                item["id"] = self.ids.new(ITEM_ID_PREFIX)
                self.template_item_ids[old_id] = item["id"]
        self.sim = self.gather(tuning, scenario, self.streams, self.ids, day=self.number)

    def opening_events(self):
        return [("day_start", {}), ("day_plan", self.plans[self.number]), ("phase_start", {})]

    def snapshot_fields(self):
        fields = {"day": self.number, "day_plan": self.plans[self.number],
                  "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades)}
        if self.sim.phase == "gather":
            fields.update(money=self.money, earned=self.earned, reputation=self.reputation)
        return fields

    def advance(self):
        phase = self.sim.phase
        if phase == "gather":
            progress = {"money": self.money, "earned": self.earned, "reputation": self.reputation}
            scenario = deepcopy(self.scenario.get("quan", {}))
            if self.template_item_ids:
                for customer in scenario.get("customers", []):
                    reserved = customer.get("reserved")
                    if isinstance(reserved, list):
                        customer["reserved"] = [self.template_item_ids.get(item_id, item_id)
                                                if isinstance(item_id, str) else item_id for item_id in reserved]
            self.sim = self.quan(self.tuning, scenario,
                                 self.streams, self.ids, inventory=self.sim.inventory_items(),
                                 day_plan=self.plans[self.number], progress=progress)
        elif phase == "quan":
            self.sim = Shop(self.tuning["shop"], self.sim, self.upgrades, self.tuning.get("freshness"))
        else:
            self.days_completed += 1
            if self.days_completed == self.days:
                self.done = True
                return []
            self.money, self.earned, self.reputation = self.sim.money, self.sim.earned, self.sim.reputation
            self.number += 1
            self._open_gather()
            return self.opening_events()
        return [("phase_start", {})]
