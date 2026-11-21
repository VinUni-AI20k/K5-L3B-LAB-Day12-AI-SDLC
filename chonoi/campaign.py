"""Mô phỏng nhiều ngày, dùng chung cho live, headless và soak."""

import math

from .ids import IdAllocator
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


class CampaignSession:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days=None, *, introductions=False):
        self.tuning = tuning
        self.scenario = scenario
        self.streams = Streams(seed)
        self.ids = IdAllocator()
        self.plans = tuning["day_plan"]
        self.days = len(self.plans) if days is None else days
        self.introductions = introductions
        initial = scenario.get("day", {})
        self.money = initial.get("money", 0)
        self.earned = initial.get("earned", 0)
        self.reputation = initial.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict.fromkeys(tuning["shop"]["upgrades"], 0)
        self.tick = self.sim_tick = self.day = 0
        self.results = []
        self.done = self.paused = False
        self.reason = None
        self._start_day()

    def _start_day(self):
        self.day += 1
        self.plan = dict(self.plans[(self.day - 1) % len(self.plans)], day=self.day)
        self.active_upgrades = self.upgrades.copy()
        self.shift_earned = 0
        gather = self.tuning["gather"].copy()
        for name, level in self.active_upgrades.items():
            if level:
                option = self.tuning["shop"]["upgrades"][name][level - 1]
                gather.update({key: option[key] for key in ("oxygen_max_s", "hp_max") if key in option})
        fixture = self.scenario.get("gather", {}).copy()
        if "monsters" in gather:
            fixture.setdefault("monsters", [m for m in gather["monsters"]["spawns"] if m["from_day"] <= self.day])
        self.sim = GatherSim({**self.tuning, "gather": gather}, fixture, self.streams, self.ids)
        self._enter("gather", "day_intro")

    def _enter(self, phase, stage):
        self.phase = phase
        self.phase_tick = 0
        self.awaiting = stage if self.introductions else None

    def proceed(self, stage):
        if not isinstance(stage, str) or stage != self.awaiting:
            raise ValueError("Màn chuyển pha đã thay đổi")
        self.awaiting = None

    @property
    def time_left_ticks(self):
        if self.phase == "shop":
            return max(0, self.tuning["shop"]["max_ticks"] - self.phase_tick)
        return self.sim.time_left_ticks

    @property
    def state(self):
        return "finished" if self.done else "paused" if self.paused else "playing"

    @property
    def score(self):
        return self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation)

    def snapshot(self):
        state = {"type": "snapshot", "mode": self.mode, "tick": self.tick, "sim_tick": self.sim_tick,
                 "phase": self.phase, "phase_tick": self.phase_tick, "state": self.state,
                 "time_left_ticks": self.time_left_ticks, "money": self.money, "earned": self.earned,
                 "reputation": self.reputation, "score": self.score, "day": self.day, "day_plan": self.plan,
                 "upgrades": self.upgrades.copy(), "active_upgrades": self.active_upgrades.copy(),
                 "shift_earned": self.shift_earned, "awaiting": self.awaiting, "days_completed": len(self.results)}
        extra = self.sim.snapshot()
        state.update({"stock": extra["stock"]} if self.phase == "shop" else extra)
        return state

    def _event(self, name, data):
        return {"type": "event", "tick": self.tick, "day": self.day, "phase": self.phase, "name": name, "data": data}

    def step(self, inp):
        if self.done or self.awaiting:
            return []
        self.tick += 1
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            rows.append(self._event("paused" if self.paused else "resumed", {}))
        if self.paused:
            return rows

        self.phase_tick += 1
        self.sim_tick += 1
        if self.phase == "shop":
            if inp.buy is not None:
                rows.append(self._buy(inp.buy))
            if inp.pressed("shop_done") or self.time_left_ticks == 0:
                result = {"day": self.day, "earned": self.earned, "reputation": self.reputation, "score": self.score}
                self.results.append(result)
                rows.append(self._event("shop_end", result))
                if self.day == self.days:
                    self.done, self.reason = True, "days_complete"
                else:
                    self._start_day()
                    rows.append(self._event("day_plan", self.plan))
            return rows

        rows.extend(self._event(name, data) for name, data in self.sim.step(inp))
        if self.phase == "quan":
            self.money, self.earned = self.sim.money, self.sim.earned
            self.reputation = self.sim.reputation
            self.shift_earned = self.earned - self._earned_at_open
            if self.sim.done:
                self._enter("shop", "day_result")
        elif self.sim.done:
            fixture = self.scenario.get("quan", {})
            stock = fixture.get("stock", self.sim.inventory_items())
            self.sim = QuanSim(self.tuning, fixture, self.streams, self.ids, inventory=stock, day_plan=self.plan)
            self._earned_at_open = self.earned
            self.sim.money, self.sim.earned = self.money, self.earned
            self.sim.reputation = self.reputation
            self._enter("quan", "evening_intro")
        return rows

    def _buy(self, upgrade):
        level = self.upgrades[upgrade]
        options = self.tuning["shop"]["upgrades"][upgrade]
        if level >= len(options):
            return self._event("buy_failed", {"upgrade": upgrade, "reason": "max_level"})
        price = options[level]["price"]
        if price > self.money:
            return self._event("buy_failed", {"upgrade": upgrade, "reason": "funds"})
        self.money -= price
        self.upgrades[upgrade] = level + 1
        return self._event("bought", {"upgrade": upgrade, "level": level + 1, "price": price, "money": self.money})

    def end_row(self):
        return {"type": "end", "mode": self.mode, "ticks": self.tick, "sim_tick": self.sim_tick,
                "state": self.state, "reason": self.reason or "tick_limit", "days_completed": len(self.results),
                "money": self.money, "earned": self.earned, "reputation": self.reputation, "score": self.score}
