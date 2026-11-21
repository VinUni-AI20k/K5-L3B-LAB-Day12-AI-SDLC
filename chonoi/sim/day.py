"""Điều phối Gather → Quán → Shop và trạng thái xuyên ngày."""

from copy import deepcopy

from ..errors import BadInput
from ..scenario import validate_day_quan
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim, gather_tuning


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.streams = streams
        self.ids = ids
        prefs = scenario.get("day", {})
        self.day = prefs.get("day", 1)
        self.days = days
        self.days_completed = 0
        self.plans = {str(plan["day"]): plan for plan in tuning["day_plan"]}
        if any(str(n) not in self.plans for n in range(self.day, self.day + days)):
            raise BadInput("lượt day vượt số ngày có trong day_plan")
        self.plans.update(prefs.get("day_plan", {}))
        self.upgrades = dict(prefs.get("upgrades", {}))
        self.money = prefs.get("money", 0)
        self.earned = prefs.get("earned", 0)
        self.reputation = prefs.get("reputation", tuning["quan"]["reputation_initial"])
        self.done = False
        self.reason = None
        self._start_gather()

    @property
    def phase(self):
        return self.inner.phase

    @property
    def time_left_ticks(self):
        return self.inner.time_left_ticks

    def phase_events(self):
        events = []
        if self.phase == "gather":
            events.extend([("day_start", {}), ("day_plan", self._plan_snapshot())])
        events.append(("phase_start", {}))
        return events

    def _plan_snapshot(self):
        return {"dishes": dict(self.plan["dishes"]), "ingredients": dict(self.plan["ingredients"])}

    def snapshot(self):
        snap = self.inner.snapshot()
        snap.update({
            "day": self.day,
            "day_plan": self._plan_snapshot(),
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        })
        return snap

    def step(self, inp):
        events = self.inner.step(inp)
        if self.phase == "gather":
            self.reputation = self.inner.reputation
            if self.inner.done:
                self._start_quan()
        elif self.phase == "quan":
            self.money = self.inner.money
            self.earned = self.inner.earned
            self.reputation = self.inner.reputation
            if self.inner.done:
                self.inner = ShopSim(self.tuning["shop"], self.inner.stock, self.money, self.upgrades)
        else:
            self.money = self.inner.money
            if self.inner.done:
                self.days_completed += 1
                if self.days_completed == self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self._start_gather()
        return events

    def _start_gather(self):
        self.plan = self.plans[str(self.day)]
        self.active_upgrades = dict(self.upgrades)
        tuning = dict(self.tuning, gather=gather_tuning(self.tuning, self.active_upgrades))
        scenario = deepcopy(self.scenario.get("gather", {}))
        if self.days_completed and "player" in scenario:
            for key in ("oxygen_ticks", "hp", "zero_oxy_ticks"):
                scenario["player"].pop(key, None)
        self.inner = GatherSim(tuning, scenario, self.streams, self.ids, day=self.day,
                               active_upgrades=self.active_upgrades)
        self.inner.reputation = self.reputation

    def _start_quan(self):
        inventory = self.inner.inventory_items()
        menu = {dish: self.tuning["menu"][dish] for dish in self.plan["dishes"]}
        scenario = deepcopy(self.scenario.get("quan", {}))
        validate_day_quan(scenario, dict(self.tuning, menu=menu), inventory)
        self.inner = QuanSim(self.tuning, scenario, self.streams, self.ids,
                             inventory=inventory, day_plan=self.plan)
        self.inner.money = self.money
        self.inner.earned = self.earned
        self.inner.reputation = self.reputation
