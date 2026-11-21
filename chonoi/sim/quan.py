"""Buổi tối — Mở Quán: đi lại, khách gọi món, giữ chỗ, nấu bếp, phục vụ, tiền/tip và kết ca."""

import math
from collections import Counter

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_items
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.reputation_multiplier = tuning["score"]["reputation_multiplier"]
        self.carry_limit = int(t.get("carry_limit", 1))
        self.rng = streams
        self.ids = ids
        self.tick_hz = tuning["tick_hz"]
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
        self.customer_interval_ticks = round(t["customer_interval_s"] * self.tick_hz)
        self.patience_max_ticks = round(t["patience_s"] * self.tick_hz)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", round(t["duration_s"] * self.tick_hz))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._load_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _load_customer(self, customer):
        loaded = dict(customer)
        loaded.setdefault("dish", loaded.pop("dish_id", None))
        loaded.setdefault("state", "waiting")
        loaded.setdefault("patience_ticks", loaded.pop("patience_ticks_left", self.patience_max_ticks))
        loaded.setdefault("eat_ticks_left", 0)
        patience = loaded["patience_ticks"]
        if type(patience) is not int or patience < 0:
            raise BadInput(f"customers.{loaded['id']}.patience_ticks phải là số nguyên không âm")
        if loaded["dish"] is not None and not isinstance(loaded["dish"], str):
            raise BadInput(f"customers.{loaded['id']}.dish phải là tên món hoặc null")
        if "reserved" not in loaded and loaded["state"] == "waiting":
            loaded["reserved"] = self.menu.get(loaded["dish"], {}).get("recipe", {})
        loaded["reserved"] = validate_items(loaded.get("reserved", {}))
        return loaded

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _compute_score(self) -> int:
        return self.earned + self.reputation_multiplier * math.floor(self.reputation)

    def snapshot(self) -> dict:
        occupied = self._occupied_tables()
        return {
            "player": {"pos": list(self.pos)},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": [dict(c, reserved=dict(c["reserved"])) for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._step_stoves(events)
        self._step_eating_customers(events)
        self._update_patience(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._try_interact(events)
        table = self._arrival_table()
        if table is not None:
            self._seat_customer(table, events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
                "score": self._compute_score(),
            }))
        return events

    @staticmethod
    def _customer_dish(c):
        return c.get("dish") or c.get("dish_id")

    @staticmethod
    def _customer_patience(c):
        return c.get("patience_ticks", c.get("patience_ticks_left", 0))

    def _has_stock_for(self, dish: str) -> bool:
        recipe = self.menu.get(dish, {}).get("recipe", {})
        return all(self.stock.get(k, 0) >= qty for k, qty in recipe.items())

    def _consume_ingredients(self, customer: dict, dish: str):
        for k, qty in self.menu[dish]["recipe"].items():
            left = self.stock.get(k, 0) - qty
            if left > 0:
                self.stock[k] = left
            else:
                self.stock.pop(k, None)
        customer["reserved"] = {}

    def _next_order_for_stove(self):
        in_flight: dict[str, int] = {}
        if self.hand:
            in_flight[self.hand] = in_flight.get(self.hand, 0) + 1
        for st in self.stoves:
            if st["state"] in ("cooking", "ready") and st.get("dish"):
                d = st["dish"]
                in_flight[d] = in_flight.get(d, 0) + 1
        for c in sort_by_id(self.customers):
            if c.get("state") in ("eating", "served"):
                continue
            d = self._customer_dish(c)
            if not d or d not in self.menu:
                continue
            if in_flight.get(d, 0) > 0:
                in_flight[d] -= 1
                continue
            if self._has_stock_for(d):
                return c, d
        return None

    def _step_stoves(self, events: list):
        for st in sort_by_id(self.stoves):
            if st["state"] == "cooking":
                st["cook_ticks_left"] = max(0, int(st["cook_ticks_left"]) - 1)
                if st["cook_ticks_left"] <= 0:
                    st["state"] = "ready"
                    st["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": st["id"], "dish": st["dish"]}))
            elif st["state"] == "ready":
                st["ready_ticks"] = int(st.get("ready_ticks", 0)) + 1

    def _interact_stove(self, st: dict, events: list) -> bool:
        if st["state"] == "ready" and self.hand is None and self.carry_limit >= 1:
            dish = st["dish"]
            self.hand = dish
            st["state"] = "idle"
            st["dish"] = None
            st["cook_ticks_left"] = 0
            st["ready_ticks"] = 0
            events.append(("dish_picked", {"dish": dish}))
            return True
        if st["state"] == "idle":
            order = self._next_order_for_stove()
            if order is not None:
                customer, dish = order
                self._consume_ingredients(customer, dish)
                st["state"] = "cooking"
                st["dish"] = dish
                st["cook_ticks_left"] = round(self.menu[dish]["cook_s"] * self.tick_hz)
                st["ready_ticks"] = 0
                events.append(("cook_started", {"stove_id": st["id"], "dish": dish}))
                return True
        return False

    def _interact_table(self, tb: dict, events: list) -> bool:
        if self.hand is None:
            return False
        for c in sort_by_id(self.customers):
            if (
                c.get("table_id") == tb["id"]
                and c.get("state") not in ("eating", "served")
                and self._customer_dish(c) == self.hand
            ):
                served_dish = self.hand
                self.hand = None
                c["state"] = "eating"
                c["eat_ticks_left"] = round(self.t["eat_s"] * self.tick_hz)
                events.append(("served", {"table_id": tb["id"], "dish": served_dish}))
                return True
        return False

    def _step_eating_customers(self, events: list):
        min_ratio = float(self.t["tip_min_patience_ratio"])
        tip_rate = float(self.t["tip_rate"])
        tip_rep = float(self.t["tip_reputation"])
        rep_min = float(self.t["reputation_min"])
        rep_max = float(self.t["reputation_max"])

        finished = set()
        for c in sort_by_id(self.customers):
            if c.get("state") != "eating":
                continue
            c["eat_ticks_left"] = max(0, int(c.get("eat_ticks_left", 0)) - 1)
            if c["eat_ticks_left"] <= 0:
                dish = self._customer_dish(c)
                price = int(self.menu[dish]["price"])
                patience = float(self._customer_patience(c))
                if self.patience_max_ticks > 0 and (patience / self.patience_max_ticks) >= min_ratio:
                    tip = round(price * tip_rate)
                    self.reputation = min(rep_max, max(rep_min, round(float(self.reputation) + tip_rep, 3)))
                else:
                    tip = 0
                total = price + tip
                self.money += total
                self.earned += total
                self.shift_earned += total
                events.append(("paid", {"customer_id": c["id"], "money": price, "tip": tip}))
                finished.add(c["id"])
        if finished:
            self.customers = [c for c in self.customers if c["id"] not in finished]

    def _try_interact(self, events: list):
        radius = float(self.t["interact_radius"])
        candidates = []
        for st in self.stoves:
            d = math.dist(self.pos, st["pos"])
            if d <= radius and (
                (st["state"] == "ready" and self.hand is None and self.carry_limit >= 1)
                or (st["state"] == "idle" and self._next_order_for_stove() is not None)
            ):
                candidates.append((d, 0, id_key(st["id"]), "stove", st))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius and self.hand is not None:
                for c in self.customers:
                    if (
                        c.get("table_id") == tb["id"]
                        and c.get("state") not in ("eating", "served")
                        and self._customer_dish(c) == self.hand
                    ):
                        candidates.append((d, 1, id_key(tb["id"]), "table", tb))
                        break
        if not candidates:
            return
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _occupied_tables(self):
        return {c["table_id"]: c["id"] for c in self.customers}

    def _update_patience(self, events):
        remaining = []
        for customer in sort_by_id(self.customers):
            if customer["state"] != "eating":
                customer["patience_ticks"] = max(0, customer["patience_ticks"] - 1)
                if customer["patience_ticks"] == 0:
                    self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {"customer_id": customer["id"], "reason": "patience_timeout"}))
                    continue
            remaining.append(customer)
        self.customers = remaining

    def _arrival_table(self):
        since_first = self.phase_tick - self.t["first_customer_tick"]
        if not self.random_customers or since_first < 0 or since_first % self.customer_interval_ticks:
            return None
        occupied = self._occupied_tables()
        return next((table for table in self.tables if table["id"] not in occupied), None)

    def _seat_customer(self, table, events):
        available = Counter(self.stock)
        for customer in self.customers:
            available.subtract(customer["reserved"])
        dishes = [dish for dish, entry in sorted(self.menu.items())
                  if all(available[kind] >= amount for kind, amount in entry["recipe"].items())]
        customer_id = self.ids.new("C")
        if not dishes:
            events.append(("no_dish", {"customer_id": customer_id}))
            return
        dish = self.rng.get("customer_order").choice(dishes)
        table_id = table["id"]
        self.customers.append({"id": customer_id, "table_id": table_id, "dish": dish, "state": "waiting",
                               "patience_ticks": self.patience_max_ticks, "eat_ticks_left": 0,
                               "reserved": dict(self.menu[dish]["recipe"])})
        events.append(("customer_arrived", {"customer_id": customer_id, "table_id": table_id, "dish": dish}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
