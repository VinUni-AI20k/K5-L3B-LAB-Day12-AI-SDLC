"""Vòng ngày (`day`) và cửa hàng nâng cấp cuối ngày (`shop`) — Test Contract v1.1."""

from __future__ import annotations

import copy

from ..ids import sort_by_id
from ..inventory import serialize_item
from ..scenario import validate_day_scenario
from .gather import GatherSim
from .quan import QuanSim


class ShopSim:
    """Cửa hàng cuối ngày: mua nâng cấp oxygen/hp áp dụng từ Ngày kế tiếp."""

    phase = "shop"

    def __init__(self, tuning: dict, leftover_stock: list[dict], day_sim: "DaySim"):
        self.tuning = tuning
        self.shop_cfg = tuning["shop"]
        self.day_sim = day_sim
        self.phase_tick = 0
        self.time_left_ticks = int(self.shop_cfg["max_ticks"])
        self.stock = sort_by_id([serialize_item(it) for it in leftover_stock])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {
            "stock": [dict(it) for it in self.stock],
        }

    def step(self, inp) -> list:
        if self.done:
            return []
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        if inp.buy is not None:
            self._handle_buy(inp.buy, events)

        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
        elif self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))
        return events

    def _handle_buy(self, action: str, events: list):
        upgrades_cfg = self.shop_cfg["upgrades"]
        if action not in upgrades_cfg:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        levels = upgrades_cfg[action]
        cur_lv = int(self.day_sim.upgrades.get(action, 0))
        nxt = next((e for e in levels if int(e["level"]) == cur_lv + 1), None)
        if nxt is None:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = int(nxt["price"])
        if self.day_sim.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.day_sim.money -= price
        self.day_sim.upgrades[action] = int(nxt["level"])
        events.append(("bought", {
            "upgrade": action,
            "level": int(nxt["level"]),
            "price": price,
            "money": self.day_sim.money,
        }))


class DaySim:
    """Điều phối chuỗi Ngày 1..N: gather -> quan -> shop."""

    mode = "day"

    def __init__(self, tuning: dict, scenario: dict, rng, ids, days: int = 1):
        self.tuning = tuning
        self.rng = rng
        self.ids = ids
        self.target_days = int(days)

        dcfg, g_tpl, q_tpl, plans = validate_day_scenario(scenario, tuning)
        self.gather_tpl = g_tpl
        self.quan_tpl = q_tpl
        self.plans = plans

        self.day = 1
        self.days_completed = 0
        self.money = int(dcfg.get("money", 0))
        self.earned = int(dcfg.get("earned", 0))
        self.reputation = float(dcfg.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = {k: int(v) for k, v in dcfg.get("upgrades", {}).items() if v > 0}
        self.active_upgrades = dict(self.upgrades)

        self.done = False
        self.reason = None
        self.phase = "gather"
        self.sub = self._new_gather()

    def current_plan(self) -> dict:
        idx = ((self.day - 1) % 5) + 1
        return self.plans[idx]

    def _new_gather(self) -> GatherSim:
        return GatherSim(
            self.tuning,
            copy.deepcopy(self.gather_tpl),
            self.rng,
            self.ids,
            day=self.day,
            active_upgrades=self.active_upgrades,
            initial_money=self.money,
            initial_earned=self.earned,
            initial_reputation=self.reputation,
        )

    def _new_quan(self, handover_inventory: dict) -> QuanSim:
        plan = self.current_plan()
        return QuanSim(
            self.tuning,
            copy.deepcopy(self.quan_tpl),
            self.rng,
            self.ids,
            inventory=handover_inventory,
            initial_money=self.money,
            initial_earned=self.earned,
            initial_reputation=self.reputation,
            allowed_dishes=list(plan["dishes"]),
        )

    @property
    def phase_tick(self) -> int:
        return self.sub.phase_tick

    @property
    def time_left_ticks(self) -> int:
        return self.sub.time_left_ticks

    def initial_events(self) -> list:
        plan = self.current_plan()
        return [
            ("gather", self.day, "day_start", {}),
            ("gather", self.day, "day_plan", {
                "dishes": dict(plan["dishes"]),
                "ingredients": dict(plan["ingredients"]),
            }),
            ("gather", self.day, "phase_start", {}),
        ]

    def snapshot(self) -> dict:
        plan = self.current_plan()
        snap = {
            "day": self.day,
            "day_plan": {
                "dishes": dict(plan["dishes"]),
                "ingredients": dict(plan["ingredients"]),
            },
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        }
        snap.update(self.sub.snapshot())
        return snap

    def step(self, inp) -> list:
        if self.done:
            return []
        cur_phase = self.phase
        cur_day = self.day
        raw_events = self.sub.step(inp)
        out = [(cur_phase, cur_day, name, data) for name, data in raw_events]

        if self.sub.done:
            if cur_phase == "gather":
                inv = self.sub.inventory_items()
                self.phase = "quan"
                self.sub = self._new_quan(inv)
                out.append(("quan", cur_day, "phase_start", {}))
            elif cur_phase == "quan":
                self.money = self.sub.money
                self.earned = self.sub.earned
                self.reputation = self.sub.reputation
                leftover = [serialize_item(it) for it in self.sub.stock]
                self.phase = "shop"
                self.sub = ShopSim(self.tuning, leftover, self)
                out.append(("shop", cur_day, "phase_start", {}))
            else:  # shop ended
                self.days_completed += 1
                if self.days_completed >= self.target_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self.active_upgrades = dict(self.upgrades)
                    self.phase = "gather"
                    self.sub = self._new_gather()
                    plan = self.current_plan()
                    out.append(("gather", self.day, "day_start", {}))
                    out.append(("gather", self.day, "day_plan", {
                        "dishes": dict(plan["dishes"]),
                        "ingredients": dict(plan["ingredients"]),
                    }))
                    out.append(("gather", self.day, "phase_start", {}))
        return out
