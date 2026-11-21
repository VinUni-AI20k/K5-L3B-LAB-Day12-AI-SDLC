"""Điều phối một vòng ngày Phase 2: gather → quán → Shop."""

import copy

from ..errors import BadInput
from ..inventory import items_out
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=5):
        self.tuning = tuning
        self.scenario = scenario
        self.streams = streams
        self.ids = ids
        self.days_limit = days
        self.day_cfg = scenario.get("day", {})
        self.money = self.day_cfg.get("money", 0)
        self.earned = self.day_cfg.get("earned", 0)
        self.reputation = self.day_cfg.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(self.day_cfg.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)
        self.days_completed = 0
        self.day = 1
        self.phase = "gather"
        self.phase_tick = 0
        self.shop_ticks = 0
        self.shop_time_left = int(tuning["shop"]["max_ticks"])
        self.done = False
        self.reason = None
        self.child = None
        self.pending_events = []
        self.plan = self._plan_for_day(self.day)
        self._start_gather()
        self.pending_events.extend([
            ("day", "day_start", {}),
            ("day", "day_plan", {"dishes": dict(self.plan["dishes"]),
                                  "ingredients": dict(self.plan["ingredients"])}),
            ("gather", "phase_start", {}),
        ])

    @property
    def time_left_ticks(self):
        return self.shop_time_left if self.phase == "shop" else self.child.time_left_ticks

    def _complete_plan(self, item, day):
        item["day"] = day
        totals = {}
        for dish_id, count in item["dishes"].items():
            for kind, amount in self.tuning["menu"][dish_id]["recipe"].items():
                totals[kind] = totals.get(kind, 0) + amount * count
        item["ingredients"] = totals
        return item

    def _plan_for_day(self, day):
        override = self.day_cfg.get("day_plan")
        if isinstance(override, list):
            item = next((p for p in override if p["day"] == day), None)
            if item is not None:
                return self._complete_plan(copy.deepcopy(item), day)
        elif isinstance(override, dict):
            item = override.get(day, override.get(str(day)))
            if item is not None:
                return self._complete_plan(copy.deepcopy(item), day)
        item = next((p for p in self.tuning["day_plan"] if p["day"] == day), None)
        if item is None:
            raise BadInput(f"không có kế hoạch cho Ngày {day}")
        return self._complete_plan(copy.deepcopy(item), day)

    def _upgraded_tuning(self):
        tuning = copy.deepcopy(self.tuning)
        for name, level in self.active_upgrades.items():
            options = tuning["shop"]["upgrades"].get(name, [])
            option = next((u for u in options if u["level"] == level), None)
            if option is None:
                continue
            for key in ("oxygen_max_s", "hp_max"):
                if key in option:
                    tuning["gather"][key] = option[key]
        return tuning

    def _start_gather(self):
        self.phase = "gather"
        self.phase_tick = 0
        gather_scenario = copy.deepcopy(self.scenario.get("gather", {}))
        if self.day > 1:
            gather_scenario.pop("hold", None)
            player = gather_scenario.get("player", {})
            # Start each morning with full upgraded stats and no carry-over timers.
            for key in ("hp", "oxygen_ticks", "zero_oxy_ticks", "invuln_ticks", "catch_cd_ticks"):
                player.pop(key, None)
        self.child = GatherSim(self._upgraded_tuning(), gather_scenario,
                               self.streams, self.ids)
        self.child.money = self.money
        self.child.earned = self.earned
        self.child.reputation = self.reputation

    def _start_quan(self):
        stock = self.child.inventory_items()
        self.phase = "quan"
        self.phase_tick = 0
        self.child = QuanSim(self.tuning, self.scenario.get("quan", {}), self.streams, self.ids,
                             inventory=stock, day_plan=self.plan)
        self.child.money = self.money
        self.child.earned = self.earned
        self.child.reputation = self.reputation

    def _start_shop(self):
        self.phase = "shop"
        self.phase_tick = 0
        self.shop_ticks = 0
        self.shop_time_left = int(self.tuning["shop"]["max_ticks"])

    def snapshot(self):
        if self.phase == "shop":
            stock = self.leftover_stock
            stock = items_out(stock) if isinstance(stock, list) else dict(stock)
            snap = {"player": {"pos": list(self.tuning["quan"]["start_pos"])},
                    "stock": stock, "hand": None,
                    "stoves": [], "tables": [], "customers": []}
        else:
            snap = self.child.snapshot()
        snap.update({"day": self.day, "day_plan": {"dishes": dict(self.plan["dishes"]),
                                                    "ingredients": dict(self.plan["ingredients"])},
                    "upgrades": dict(self.upgrades), "active_upgrades": dict(self.active_upgrades),
                    "days_completed": self.days_completed, "phase": self.phase,
                    "phase_tick": self.phase_tick, "time_left_ticks": self.time_left_ticks,
                    "money": self.money, "earned": self.earned, "reputation": self.reputation})
        return snap

    def step(self, inp):
        if self.done:
            return []
        if self.phase == "shop":
            return self._step_shop(inp)
        old_phase = self.phase
        events = self.child.step(inp)
        self.phase_tick = self.child.phase_tick
        if self.child.done and old_phase == "gather":
            self.money, self.earned, self.reputation = self.child.money, self.child.earned, self.child.reputation
            self._start_quan()
            return [(old_phase, name, data) for name, data in events] + [("quan", "phase_start", {})]
        if self.child.done and old_phase == "quan":
            self.money, self.earned, self.reputation = self.child.money, self.child.earned, self.child.reputation
            self.leftover_stock = copy.deepcopy(self.child.stock)
            self._start_shop()
            return [(old_phase, name, data) for name, data in events] + [("shop", "phase_start", {})]
        return [(old_phase, name, data) for name, data in events]

    def _step_shop(self, inp):
        self.phase_tick += 1
        self.shop_ticks += 1
        self.shop_time_left = max(0, int(self.tuning["shop"]["max_ticks"]) - self.shop_ticks)
        events = []
        upgrade = inp.actions.get("buy")
        if upgrade is not None:
            options = self.tuning["shop"]["upgrades"].get(upgrade)
            if options is None:
                events.append(("shop", "buy_failed", {"action": upgrade, "reason": "unknown"}))
            else:
                level = self.upgrades.get(upgrade, 0) + 1
                option = next((u for u in options if u["level"] == level), None)
                if option is None:
                    events.append(("shop", "buy_failed", {"action": upgrade, "reason": "max_level"}))
                elif self.money < option["price"]:
                    events.append(("shop", "buy_failed", {"action": upgrade, "reason": "funds"}))
                else:
                    self.money -= option["price"]
                    self.upgrades[upgrade] = level
                    events.append(("shop", "bought", {"upgrade": upgrade, "level": level,
                                                          "price": option["price"], "money": self.money}))
        reason = "done" if inp.pressed("shop_done") else "time" if self.shop_time_left == 0 else None
        if reason:
            events.append(("shop", "shop_end", {"reason": reason}))
            self.days_completed += 1
            if self.day == self.days_limit:
                self.done = True
                self.reason = "days_complete"
            else:
                self.day += 1
                self.active_upgrades = dict(self.upgrades)
                self.plan = self._plan_for_day(self.day)
                self._start_gather()
                events.extend([("day", "day_start", {}),
                               ("day", "day_plan", {"dishes": dict(self.plan["dishes"]),
                                                    "ingredients": dict(self.plan["ingredients"])}),
                               ("gather", "phase_start", {})])
        return events
