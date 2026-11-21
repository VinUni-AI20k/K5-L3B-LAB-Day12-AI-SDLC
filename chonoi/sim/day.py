"""Một Ngày: bàn giao kho giữ trong bộ nhớ từ buổi sáng sang buổi tối.

Mode day ở contract hiện tại chỉ ghép GatherSim và QuanSim, chưa thêm Shop.
"""

from ..inventory import hold_to_items, merge_items
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        gather_scenario = scenario.get("gather", {}) if isinstance(scenario, dict) else {}
        self.quan_scenario = scenario.get("quan", {}) if isinstance(scenario, dict) else {}
        self.initial_inventory = dict(inventory or {})
        self.inventory = dict(self.initial_inventory)
        self.gather = GatherSim(tuning, gather_scenario, streams, ids)
        self.quan = None
        self.done = False
        self.reason = None
        self.elapsed_ticks = 0

    def inventory_items(self) -> dict:
        if self.phase == "gather":
            return merge_items(self.initial_inventory, hold_to_items(self.gather.hold))
        return dict(self.quan.stock)

    def snapshot(self) -> dict:
        snap = self.gather.snapshot() if self.phase == "gather" else self.quan.snapshot()
        snap["day"] = 1
        snap["mode"] = "day"
        snap["phase"] = self.phase
        return snap

    @property
    def money(self):
        return self.gather.money if self.phase == "gather" else self.quan.money

    @property
    def earned(self):
        return self.gather.earned if self.phase == "gather" else self.quan.earned

    @property
    def reputation(self):
        return self.gather.reputation if self.phase == "gather" else self.quan.reputation

    @property
    def time_left_ticks(self):
        return self.gather.time_left_ticks if self.phase == "gather" else self.quan.time_left_ticks

    def step(self, inp):
        self.elapsed_ticks += 1
        if self.phase == "gather":
            events = self.gather.step(inp)
            if self.gather.done:
                gathered = hold_to_items(self.gather.hold)
                self.inventory = merge_items(self.initial_inventory, gathered)
                self.quan = QuanSim(
                    self.tuning,
                    dict(self.quan_scenario),
                    self.rng,
                    self.ids,
                    inventory=self.inventory,
                )
                self.phase = "quan"
                events.append(("phase_start", {
                    "day": 1,
                    "phase": "quan",
                    "inventory": {"items": dict(self.inventory)},
                }))
            return events

        events = self.quan.step(inp)
        if self.quan.done:
            self.done = True
            self.reason = self.quan.reason
        return events
