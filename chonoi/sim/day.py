"""Compose gather, quan and the Shop without resetting the outer clock."""

from .gather import GatherSim
from .quan import QuanSim
from ..day_config import day_plans, gather_tuning
from ..ids import IdAllocator
from ..rng import Streams


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days):
        self.tuning = tuning
        self.gather_scenario = scenario.get("gather", {})
        self.quan_scenario = scenario.get("quan", {})
        self.streams = Streams(seed)
        self.ids = IdAllocator()
        initial = scenario.get("day", {})
        self.plans = day_plans(tuning, initial.get("day_plan", ()))
        self.money = initial.get("money", 0)
        self.earned = initial.get("earned", 0)
        self.reputation = initial.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = initial.get("upgrades", {}).copy()
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.done = False
        self.reason = None
        self._start_day()

    def _start_day(self):
        self.active_upgrades = self.upgrades.copy()
        self.plan = self.plans[self.day]
        self.phase = "gather"
        effective = gather_tuning(self.tuning, self.active_upgrades)
        self.current = GatherSim(effective, self.gather_scenario, self.streams, self.ids,
                                 day=self.day, active_upgrades=self.active_upgrades)
        self.current.reputation = self.reputation

    def _start_quan(self, stock):
        menu = {dish: self.tuning["menu"][dish] for dish in self.plan["dishes"]}
        tuning = {**self.tuning, "menu": menu}
        scenario = {**self.quan_scenario, "reputation": self.reputation}
        self.current = QuanSim(tuning, scenario, self.streams, self.ids, inventory=stock)
        self.current.money = self.money
        self.current.earned = self.earned
        self.phase = "quan"

    def _start_shop(self):
        self.shop_stock = {kind: count for kind, count in self.current.stock.items() if count}
        self.current = None
        self.shop_ticks = self.tuning["shop"]["max_ticks"]
        self.phase = "shop"

    @property
    def time_left_ticks(self):
        return self.shop_ticks if self.phase == "shop" else self.current.time_left_ticks

    def snapshot(self):
        state = {"stock": self.shop_stock.copy()} if self.phase == "shop" else self.current.snapshot()
        return {**state, "day": self.day, "day_plan": self.plan,
                "upgrades": self.upgrades.copy(), "active_upgrades": self.active_upgrades.copy()}

    def start_events(self):
        return [("day_start", {}), ("day_plan", {k: self.plan[k] for k in ("dishes", "ingredients")}),
                ("phase_start", {})]

    def step(self, inp):
        """Return events from the phase that owns this gameplay step."""
        if self.phase == "shop":
            return self._step_shop(inp)
        events = self.current.step(inp)
        self.reputation = self.current.reputation
        if self.phase == "quan":
            self.money = self.current.money
            self.earned = self.current.earned
        return events

    def advance_phase(self, events):
        """Transition after the old phase's events have been stamped."""
        if self.phase == "gather" and self.current.done:
            _, end = events[-1]
            self._start_quan(end["inventory"]["items"])
            return [("phase_start", {})]
        if self.phase == "quan" and self.current.done:
            self._start_shop()
            return [("phase_start", {})]
        if self.phase == "shop" and events and events[-1][0] == "shop_end":
            self.days_completed += 1
            self.shop_stock = {}
            if self.days_completed == self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self._start_day()
                return self.start_events()
        return []

    def _step_shop(self, inp):
        events = []
        if inp.buy is not None:
            events.append(self._buy(inp.buy))
        self.shop_ticks -= 1
        if inp.pressed("shop_done"):
            events.append(("shop_end", {"reason": "done"}))
        elif self.shop_ticks == 0:
            events.append(("shop_end", {"reason": "time"}))
        return events

    def _buy(self, action):
        levels = self.tuning["shop"]["upgrades"].get(action)
        current_level = self.upgrades.get(action, 0)
        if levels is None:
            reason = "unknown"
        elif current_level >= len(levels):
            reason = "max_level"
        else:
            target = levels[current_level]
            price = target["price"]
            if self.money >= price:
                self.money -= price
                self.upgrades[action] = target["level"]
                return ("bought", {"upgrade": action, "level": target["level"], "price": price,
                                   "money": self.money})
            reason = "funds"
        return ("buy_failed", {"action": action, "reason": reason})
