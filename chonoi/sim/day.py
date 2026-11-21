"""TICKET-02: deterministic gather → quan → shop, shared by CLI and live."""
from copy import deepcopy
from ..errors import BadInput
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning, self.scenario = tuning, scenario
        self.streams, self.ids = streams, ids
        self.days = days
        self.day = 1
        self.days_completed = 0
        data = scenario.get("day", {})
        self.money = data.get("money", 0)
        self.earned = data.get("earned", 0)
        self.reputation = data.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(data.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = data.get("day_plan", tuning["day_plan"])
        self.done, self.reason = False, None
        self.stock = {}
        self.sales = {}
        self.stats = {}
        self._new_day()
        self.initial_events = self._day_events()

    @property
    def phase_tick(self):
        return self._phase_tick if self.phase == "shop" else self.active.phase_tick

    @property
    def time_left_ticks(self):
        return self.shop_left if self.phase == "shop" else self.active.time_left_ticks

    def _event(self, name, data=None, phase=None, day=None):
        return {"phase": phase or self.phase, "day": day or self.day,
                "name": name, "data": {} if data is None else data}

    def _day_events(self):
        return [self._event("day_start"), self._event("day_plan", self.day_plan),
                self._event("phase_start")]

    def _new_day(self):
        self.active_upgrades = dict(self.upgrades)
        self.day_plan = deepcopy(self.plans[self.day - 1])
        self.day_plan.pop("day", None)
        self.phase = "gather"
        self.effective_tuning = deepcopy(self.tuning)
        g = self.effective_tuning["gather"]
        for kind, level in self.active_upgrades.items():
            if level:
                row = self.tuning["shop"]["upgrades"][kind][level - 1]
                field = "oxygen_max_s" if kind == "oxygen" else "hp_max"
                g[field] = row[field]
        sc = deepcopy(self.scenario.get("gather", {}))
        sc["day"] = self.day
        self.active = GatherSim(self.effective_tuning, sc, self.streams, self.ids)
        self.stats = {"served": 0, "left": 0, "money": 0, "tips": 0,
                      "reputation_start": self.reputation, "reputation_delta": 0}
        self.stock = {}

    def _carry(self):
        return {"money": self.money, "earned": self.earned, "reputation": self.reputation}

    def snapshot(self):
        body = {"stock": dict(self.stock)} if self.phase == "shop" else self.active.snapshot()
        body.update(day=self.day, day_plan=deepcopy(self.day_plan),
                    upgrades=dict(self.upgrades), active_upgrades=dict(self.active_upgrades),
                    days_completed=self.days_completed, day_result=dict(self.stats), sales=dict(self.sales))
        if self.phase == "shop":
            body["shop"] = deepcopy(self.tuning["shop"])
        return body

    def step(self, inp):
        if self.done:
            return []
        if self.phase == "shop":
            return self._shop_step(inp)
        old_phase = self.phase
        events = []
        for name, data in self.active.step(inp):
            events.append(self._event(name, data))
            if name == "served":
                self.stats["served"] += 1
            elif name == "customer_left":
                self.stats["left"] += 1
            elif name == "paid":
                self.stats["money"] += data["amount"]
                self.stats["tips"] += data["tip"]
                # The order still exists in the final snapshot only until payment.
                dish = self._orders.get(data["order_id"])
                if dish:
                    self.sales[dish] = self.sales.get(dish, 0) + 1
            elif name == "customer_arrived":
                self._orders[data["order_id"]] = data["dish_id"]
        if old_phase == "quan":
            self.money, self.earned, self.reputation = self.active.money, self.active.earned, self.active.reputation
            self.stats["reputation_delta"] = self.reputation - self.stats["reputation_start"]
        if not self.active.done:
            return events
        if old_phase == "gather":
            self.stock = self.active.inventory_items()
            self.active = QuanSim(self.tuning, deepcopy(self.scenario.get("quan", {})),
                                  self.streams, self.ids, inventory=self.stock,
                                  plan_dishes=self.day_plan["dishes"], carry=self._carry())
            self._orders = {c["id"]: c["dish_id"] for c in self.active.customers}
            self.phase = "quan"
        else:
            self.stock = dict(self.active.stock)
            self.phase = "shop"
            self._phase_tick = 0
            self.shop_left = self.tuning["shop"]["max_ticks"]
        events.append(self._event("phase_start"))
        return events

    def _shop_step(self, inp):
        self._phase_tick += 1
        self.shop_left -= 1
        events = []
        if inp.buy is not None:
            kind = inp.buy
            rows = self.tuning["shop"]["upgrades"].get(kind)
            level = self.upgrades.get(kind, 0)
            reason = ("unknown" if rows is None else "max_level" if level >= len(rows)
                      else "funds" if self.money < rows[level]["price"] else None)
            if reason:
                events.append(self._event("buy_failed", {"action": kind, "reason": reason}))
            else:
                row = rows[level]
                self.money -= row["price"]
                self.upgrades[kind] = row["level"]
                events.append(self._event("bought", {"upgrade": kind, "level": row["level"],
                                                       "price": row["price"], "money": self.money}))
        if inp.pressed("shop_done") or self.shop_left <= 0:
            events.append(self._event("shop_end", {"reason": "done" if inp.pressed("shop_done") else "time"}))
            self.days_completed += 1
            if self.days_completed == self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self._new_day()
                events.extend(self._day_events())
        return events
