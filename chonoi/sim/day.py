"""Điều phối một vòng ngày Phase 2/3: gather → quán → Shop."""

import copy
from fractions import Fraction

from ..errors import BadInput
from ..ids import IdAllocator, id_key, sort_by_id
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
        self.day_reservations = self._prepare_day_reservations()
        self._validate_reservations_for_run()
        self._start_gather()
        self.pending_events.extend([
            ("day", "day_start", {}),
            ("day", "day_plan", {"dishes": dict(self.plan["dishes"]),
                                  "ingredients": dict(self.plan["ingredients"])}),
            ("gather", "phase_start", {}),
        ])
        self.pending_events.extend(self._reservation_publish_events())

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
        plan_day = ((day - 1) % 5) + 1
        override = self.day_cfg.get("day_plan")
        if isinstance(override, list):
            item = next((p for p in override if p["day"] == day), None)
            if item is None:
                item = next((p for p in override if p["day"] == plan_day), None)
            if item is not None:
                return self._complete_plan(copy.deepcopy(item), day)
        elif isinstance(override, dict):
            item = override.get(day, override.get(str(day)))
            if item is None:
                item = override.get(plan_day, override.get(str(plan_day)))
            if item is not None:
                return self._complete_plan(copy.deepcopy(item), day)
        item = next((p for p in self.tuning["day_plan"] if p["day"] == plan_day), None)
        if item is None:
            raise BadInput(f"không có kế hoạch cho Ngày {day}")
        return self._complete_plan(copy.deepcopy(item), day)

    def _prepare_day_reservations(self):
        qscenario = self.scenario.get("quan", {})
        if "reservations" in qscenario:
            reservations = [dict(r, state=r.get("state", "scheduled"))
                           for r in copy.deepcopy(qscenario["reservations"])]
            if any(r["dish_id"] not in self.plan["dishes"] for r in reservations):
                raise BadInput(f"Ngày {self.day}: món trong đơn đặt trước phải thuộc day_plan")
            return reservations
        if qscenario.get("random_reservations", True) is False:
            return []
        cfg = self.tuning["quan"]["reservations"]
        tables = sort_by_id(self.tuning["quan"]["tables"])
        dishes = sorted(self.plan["dishes"])
        arrivals = self.streams.get("quan_reservation_arrival")
        choices = self.streams.get("quan_reservation_dish")
        reservations = []
        reservation_ids = IdAllocator()
        for i in range(min(cfg["count"], len(tables))):
            reservations.append({"id": reservation_ids.new("R"), "table_id": tables[i]["id"],
                                 "dish_id": choices.choice(dishes),
                                 "arrival_tick": arrivals.randint(1800, 10799), "state": "scheduled"})
        return reservations

    def _validate_reservations_for_run(self):
        fixtures = self.scenario.get("quan", {}).get("reservations")
        if fixtures is None:
            return
        for day in range(1, self.days_limit + 1):
            plan = self._plan_for_day(day)
            if any(r["dish_id"] not in plan["dishes"] for r in fixtures):
                raise BadInput(f"Ngày {day}: món trong đơn đặt trước phải thuộc day_plan")

    def _reservation_publish_events(self):
        return [("day", "reservation_published",
                 {key: reservation[key] for key in ("id", "table_id", "dish_id", "arrival_tick")})
                for reservation in sorted(self.day_reservations, key=lambda r: id_key(r["id"]))]

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
            # The fixture's day-one items recur as fresh stock with new,
            # never-reused IDs on subsequent days.
            source = gather_scenario.get("hold", [])
            initial = Fraction(str(self.tuning["freshness"]["initial"]))
            gather_scenario["hold"] = [
                {"id": self.ids.new("I"), "kind": item["kind"], "fresh": initial}
                for item in source
            ]
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
        quan_scenario = copy.deepcopy(self.scenario.get("quan", {}))
        quan_scenario["reservations"] = copy.deepcopy(self.day_reservations)
        quan_scenario["random_reservations"] = False
        self.child = QuanSim(self.tuning, quan_scenario, self.streams, self.ids,
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
        if self.phase in ("gather", "shop"):
            snap["reservations"] = [dict(r) for r in self.day_reservations]
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
        self.money, self.earned, self.reputation = (
            self.child.money, self.child.earned, self.child.reputation)
        if self.child.done and old_phase == "gather":
            self._start_quan()
            return [(old_phase, name, data) for name, data in events] + [("quan", "phase_start", {})]
        if self.child.done and old_phase == "quan":
            self.day_reservations = copy.deepcopy(self.child.reservations)
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
            closing_day = self.day
            events.append(("shop", "shop_end", {"reason": reason}, closing_day))
            self.days_completed += 1
            if self.day == self.days_limit:
                self.done = True
                self.reason = "days_complete"
            else:
                self.day += 1
                self.active_upgrades = dict(self.upgrades)
                self.plan = self._plan_for_day(self.day)
                self.day_reservations = self._prepare_day_reservations()
                self._start_gather()
                events.extend([("day", "day_start", {}, self.day),
                               ("day", "day_plan", {"dishes": dict(self.plan["dishes"]),
                                                    "ingredients": dict(self.plan["ingredients"])}, self.day),
                               ("gather", "phase_start", {}, self.day)])
                events.extend((*event, self.day) for event in self._reservation_publish_events())
        return events
