"""Vòng ngày (`--mode day --days 1..5`): gather -> quan -> shop -> ngày kế / days_complete."""

import copy

from .gather import GatherSim
from .quan import QuanSim
from ..ids import IdAllocator
from ..rng import Streams


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.seed = seed
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0

        day_cfg = scenario.get("day", {})
        self.money = day_cfg.get("money", 0)
        self.earned = day_cfg.get("earned", 0)
        self.reputation = day_cfg.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(day_cfg.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)

        self.plans = {p["day"]: copy.deepcopy(p) for p in tuning["day_plan"]}
        for ov in day_cfg.get("day_plan", []):
            d = ov["day"]
            dishes = dict(ov["dishes"])
            ingredients = {}
            for did, cnt in dishes.items():
                for ing, amt in tuning["menu"][did]["recipe"].items():
                    ingredients[ing] = ingredients.get(ing, 0) + amt * cnt
            self.plans[d] = {"day": d, "dishes": dishes, "ingredients": ingredients}

        self._shop_stock = {}
        self._shop_time_left = 0
        self.done = False
        self.reason = None
        self._sub = None
        self._build_gather()

    @property
    def time_left_ticks(self):
        if self.phase == "shop":
            return self._shop_time_left
        return self._sub.time_left_ticks

    def _current_plan(self):
        return self.plans[self.day]

    def _day_tuning(self):
        t = copy.deepcopy(self.tuning)
        shop_ups = t.get("shop", {}).get("upgrades", {})
        oxy_lvl = self.active_upgrades.get("oxygen", 0)
        if oxy_lvl > 0:
            entry = next((u for u in shop_ups.get("oxygen", []) if u["level"] == oxy_lvl), None)
            if entry:
                t["gather"]["oxygen_max_s"] = entry["oxygen_max_s"]
        hp_lvl = self.active_upgrades.get("hp", 0)
        if hp_lvl > 0:
            entry = next((u for u in shop_ups.get("hp", []) if u["level"] == hp_lvl), None)
            if entry:
                t["gather"]["hp_max"] = entry["hp_max"]
        plan = self._current_plan()
        t["menu"] = {did: t["menu"][did] for did in sorted(plan["dishes"]) if did in t["menu"]}
        return t

    def _build_gather(self):
        dt = self._day_tuning()
        g_sc = self.scenario.get("gather", {})
        self._sub = GatherSim(dt, g_sc, Streams(self.seed + self.day * 1000), IdAllocator(), day=self.day)
        self._sub.money = self.money
        self._sub.earned = self.earned
        self._sub.reputation = self.reputation

    def _build_quan(self, inventory):
        dt = self._day_tuning()
        q_sc = dict(self.scenario.get("quan", {}))
        q_sc["reputation"] = self.reputation
        self._sub = QuanSim(dt, q_sc, Streams(self.seed + self.day * 1000 + 1), IdAllocator(), inventory=inventory)
        self._sub.money = self.money
        self._sub.earned = self.earned

    def initial_events(self):
        plan = self._current_plan()
        return [
            ("day_start", {}, "gather", self.day),
            ("day_plan", {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])}, "gather", self.day),
            ("phase_start", {}, "gather", self.day),
        ]

    def live_hints(self) -> dict:
        if self.phase == "shop" or self._sub is None:
            return {}
        return self._sub.live_hints()

    def snapshot(self) -> dict:
        plan = self._current_plan()
        base = {
            "day": self.day,
            "day_plan": {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])},
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        }
        if self.phase == "shop":
            base.update({"stock": dict(self._shop_stock), "time_left_ticks": self._shop_time_left})
        else:
            base.update(self._sub.snapshot())
        return base

    def step(self, inp):
        out = []
        if self.phase == "gather":
            self.phase_tick += 1
            for name, data in self._sub.step(inp):
                out.append((name, data, "gather", self.day))
            if self._sub.done:
                inv = self._sub.inventory_items()
                self._build_quan(inv)
                self.phase = "quan"
                self.phase_tick = 0
                out.append(("phase_start", {}, "quan", self.day))
        elif self.phase == "quan":
            self.phase_tick += 1
            for name, data in self._sub.step(inp):
                out.append((name, data, "quan", self.day))
            self.money = self._sub.money
            self.earned = self._sub.earned
            self.reputation = self._sub.reputation
            if self._sub.done:
                self._shop_stock = {k: v for k, v in sorted(self._sub.stock.items()) if v > 0}
                self._shop_time_left = self.tuning["shop"]["max_ticks"]
                self.phase = "shop"
                self.phase_tick = 0
                out.append(("phase_start", {}, "shop", self.day))
        elif self.phase == "shop":
            self.phase_tick += 1
            self._shop_time_left = max(0, self._shop_time_left - 1)
            if inp.buy:
                self._buy(inp.buy, out)
            end_reason = "done" if inp.pressed("shop_done") else ("time" if self._shop_time_left <= 0 else None)
            if end_reason is not None:
                out.append(("shop_end", {"reason": end_reason}, "shop", self.day))
                self.days_completed += 1
                self._shop_stock = {}
                if self.day >= self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self.active_upgrades = dict(self.upgrades)
                    self._build_gather()
                    self.phase = "gather"
                    self.phase_tick = 0
                    plan = self._current_plan()
                    out.append(("day_start", {}, "gather", self.day))
                    out.append(("day_plan", {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])}, "gather", self.day))
                    out.append(("phase_start", {}, "gather", self.day))
        return out

    def _buy(self, action: str, out):
        shop_ups = self.tuning.get("shop", {}).get("upgrades", {})
        if action not in shop_ups:
            out.append(("buy_failed", {"action": action, "reason": "unknown"}, "shop", self.day))
            return
        levels = sorted(shop_ups[action], key=lambda u: u["level"])
        cur = self.upgrades.get(action, 0)
        nxt = next((u for u in levels if u["level"] == cur + 1), None)
        if nxt is None:
            out.append(("buy_failed", {"action": action, "reason": "max_level"}, "shop", self.day))
            return
        price = nxt["price"]
        if self.money < price:
            out.append(("buy_failed", {"action": action, "reason": "funds"}, "shop", self.day))
            return
        self.money -= price
        self.upgrades[action] = nxt["level"]
        out.append(("bought", {"upgrade": action, "level": nxt["level"], "price": price, "money": self.money}, "shop", self.day))
