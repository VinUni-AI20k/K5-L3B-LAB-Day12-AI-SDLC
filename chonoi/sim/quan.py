"""Buổi tối — Mở Quán (PRD-0 mục F)."""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        patience_ticks = int(round(t["patience_s"] * TICK))
        self.customers = []
        missing_reservations = set()
        for source in scenario.get("customers", []):
            customer = dict(source)
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("patience_ticks_left", patience_ticks)
            customer.setdefault("order_status", "reserved")
            if "reserved" not in customer:
                missing_reservations.add(customer["id"])
            customer.setdefault("reserved", {})
            self.customers.append(customer)
        # Rebuild omitted fixture reservations in the contract's stable order.
        for customer in sorted(self.customers, key=lambda c: (
                c["order_tick"], id_key(c["table_id"]), id_key(c["id"]))):
            if customer["id"] in missing_reservations and customer["order_status"] == "reserved":
                recipe = self.menu.get(customer.get("dish_id"), {}).get("recipe", {})
                customer["reserved"] = dict(recipe)
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # Timers advance before movement and interaction. Remember which dishes
        # were already ready so newly cooked dishes start at ready_ticks == 0.
        ready_at_start = {s["id"] for s in self.stoves if s["state"] == "ready"}
        for stove in self.stoves:
            if stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    dish = stove["dish"]
                    events.append(("dish_ready", {"stove_id": stove["id"],
                                                   "order_id": dish["order_id"],
                                                   "dish_id": dish["dish_id"]}))
            elif stove["state"] == "ready" and stove["id"] in ready_at_start:
                stove["ready_ticks"] += 1
        # Existing eating customers count this tick. Newly served customers do
        # not begin eating until the next tick.
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer.get("state") == "eating":
                customer["eat_ticks_left"] = max(0, customer["eat_ticks_left"] - 1)
        for customer in sort_by_id(self.customers):
            if customer.get("state") == "waiting":
                customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)
        self._move(inp)

        if inp.pressed("interact"):
            target = self._nearest_interaction()
            if target is not None:
                kind, entity = target
                if kind == "stove":
                    self._interact_stove(entity, events)
                else:
                    self._interact_table(entity, events)

        # Eating ends automatically, after the interaction, in table order.
        for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
            if customer.get("state") == "eating" and customer["eat_ticks_left"] == 0:
                self._pay_and_leave(customer, "finished_eating", events)

        # Patience is resolved after interaction, so serving at exactly zero is
        # valid. Closing takes precedence over a patience timeout on that tick.
        if self.time_left_ticks > 0:
            for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
                if customer.get("state") == "waiting" and customer["patience_ticks_left"] == 0:
                    self._customer_left(customer, "patience", events)

        if self.time_left_ticks <= 0:
            for customer in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
                if customer.get("state") == "eating":
                    self._pay_and_leave(customer, "closing", events)
                else:
                    self._customer_left(customer, "closing", events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events

        if self.random_customers:
            first = int(self.t["first_customer_tick"])
            interval = int(round(self.t["customer_interval_s"] * TICK))
            if self.phase_tick >= first and (self.phase_tick - first) % interval == 0:
                self._arrive_customer(events)
        return events

    def _nearest_interaction(self):
        candidates = []
        radius = self.t["interact_radius"]
        for stove in self.stoves:
            distance = math.dist(self.pos, stove["pos"])
            if distance <= radius:
                candidates.append((distance, 0, id_key(stove["id"]), "stove", stove))
        for table in self.tables:
            distance = math.dist(self.pos, table["pos"])
            if distance <= radius:
                candidates.append((distance, 1, id_key(table["id"]), "table", table))
        if not candidates:
            return None
        chosen = min(candidates, key=lambda item: item[:3])
        return chosen[3], chosen[4]

    def _interact_stove(self, stove, events):
        if stove["state"] == "idle":
            orders = [c for c in self.customers if c.get("order_status") == "reserved"]
            if not orders:
                return
            customer = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"]), id_key(c["id"])))
            recipe = dict(customer["reserved"])
            dish = self.menu[customer["dish_id"]]
            # Reserved stock is consumed only when cooking starts.
            for kind, amount in recipe.items():
                self.stock[kind] -= amount
            customer["reserved"] = {}
            customer["order_status"] = "assigned"
            payload = {"order_id": customer["id"], "dish_id": customer["dish_id"],
                       "base_price": dish["price"]}
            stove["state"] = "cooking"
            stove["dish"] = payload
            stove["cook_ticks_left"] = int(round(dish["cook_s"] * TICK))
            stove["ready_ticks"] = 0
            items = [kind for kind in sorted(recipe) for _ in range(recipe[kind])]
            events.append(("cook_started", {"stove_id": stove["id"], "order_id": customer["id"],
                                             "dish_id": customer["dish_id"], "items": items,
                                             "base_price": dish["price"]}))
        elif stove["state"] == "ready" and self.hand is None:
            payload = dict(stove["dish"])
            self.hand = payload
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": stove["id"],
                                            "order_id": payload["order_id"],
                                            "dish_id": payload["dish_id"]}))

    def _interact_table(self, table, events):
        if self.hand is None:
            return
        customer = next((c for c in self.customers
                         if c["id"] == self.hand["order_id"] and c["table_id"] == table["id"]
                         and c.get("state") == "waiting"), None)
        if customer is None:
            return
        payload = self.hand
        self.hand = None
        max_patience = int(round(self.t["patience_s"] * TICK))
        ratio = customer["patience_ticks_left"] / max_patience
        tip = (math.floor(payload["base_price"] * self.t["tip_rate"])
               if ratio >= self.t["tip_min_patience_ratio"] else 0)
        customer["state"] = "eating"
        customer["order_status"] = "served"
        customer["reserved"] = {}
        customer["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        customer["base_price"] = payload["base_price"]
        customer["tip"] = tip
        events.append(("served", {"order_id": customer["id"], "table_id": table["id"],
                                   "dish_id": customer["dish_id"],
                                   "patience_ticks_left": customer["patience_ticks_left"],
                                   "base_price": payload["base_price"], "tip": tip}))

    def _pay_and_leave(self, customer, reason, events):
        amount = customer["base_price"] + customer["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        events.append(("paid", {"order_id": customer["id"], "table_id": customer["table_id"],
                                 "base_price": customer["base_price"], "tip": customer["tip"],
                                 "amount": amount, "reason": reason}))
        if customer["tip"] > 0:
            self.reputation = min(self.t["reputation_max"], max(
                self.t["reputation_min"], self.reputation + self.t["tip_reputation"]))
        self.customers.remove(customer)

    def _discard_customer_dish(self, customer):
        order_id = customer["id"]
        for stove in self.stoves:
            dish = stove.get("dish")
            if dish is not None and dish.get("order_id") == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand.get("order_id") == order_id:
            self.hand = None

    def _reserved_totals(self):
        totals = {}
        for customer in self.customers:
            if customer.get("order_status") == "reserved":
                for kind, amount in customer.get("reserved", {}).items():
                    totals[kind] = totals.get(kind, 0) + amount
        return totals

    def _available_stock(self):
        reserved = self._reserved_totals()
        return {kind: amount - reserved.get(kind, 0) for kind, amount in self.stock.items()}

    def _customer_left(self, customer, reason, events):
        if reason == "patience":
            q = self.t
            self.reputation = min(q["reputation_max"], max(
                q["reputation_min"], self.reputation + q["left_reputation_delta"]))
        self._discard_customer_dish(customer)
        self.customers.remove(customer)
        events.append(("customer_left", {"order_id": customer["id"],
                                          "table_id": customer["table_id"],
                                          "reason": reason,
                                          "reputation": self.reputation}))

    def _arrive_customer(self, events):
        occupied = {customer["table_id"] for customer in self.customers}
        free_tables = [table for table in self.tables if table["id"] not in occupied]
        if not free_tables:
            return
        table = sort_by_id(free_tables)[0]
        available = self._available_stock()
        dish_ids = sorted(
            dish_id for dish_id, dish in self.menu.items()
            if all(available.get(kind, 0) >= amount for kind, amount in dish["recipe"].items())
        )
        if not dish_ids:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("quan_customer_orders").choice(dish_ids)
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": dict(self.menu[dish_id]["recipe"]),
        }
        self.customers.append(customer)
        events.append(("customer_arrived", {"order_id": customer_id,
                                              "table_id": table["id"],
                                              "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
