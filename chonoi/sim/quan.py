"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phase 1 (PRD-0 mục F, Quán):
  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), truy vấn điều kiện no_dish.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from copy import deepcopy

from ..errors import BadInput
from ..ids import sort_by_id
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
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
        random_customers = scenario.get("random_customers", True)
        if not isinstance(random_customers, bool):
            raise BadInput("quan.random_customers phải là boolean")
        self.random_customers = random_customers
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        self._reservation_state = {}
        for source in sort_by_id(scenario.get("customers", [])):
            c = deepcopy(source)
            dish_id = c.get("dish_id") or c.get("dish") or c.get("order")
            state = c.get("state", "waiting")
            if "dish_id" not in c:
                c["dish_id"] = dish_id
            c["state"] = state
            if "patience_ticks_left" in c:
                patience = int(c["patience_ticks_left"])
            elif "patience_ticks" in c:
                patience = int(c["patience_ticks"])
            elif "patience_s" in c:
                patience = int(round(float(c["patience_s"]) * self.tick_hz))
            else:
                patience = int(round(t["patience_s"] * self.tick_hz))
            c["patience_ticks_left"] = patience
            c["patience_ticks"] = patience
            c["patience_max_ticks"] = c.get(
                "patience_max_ticks", int(round(t["patience_s"] * self.tick_hz)))
            eat_ticks = c.get("eat_ticks_left")
            if eat_ticks is None:
                eat_ticks = int(round(t["eat_s"] * self.tick_hz))
            c["eat_ticks_left"] = int(eat_ticks)
            if state in ("ordered", "eating"):
                reserved = deepcopy(c.get("reserved", {}))
                if any(reserved.values()):
                    raise BadInput(f"customers.{c['id']}: khách đã nấu không giữ nguyên liệu thô")
                reservation_state = "consumed"
            elif "reserved" in c:
                reserved = deepcopy(c["reserved"])
                reservation_state = "reserved" if any(reserved.values()) else "released"
            elif self.hand == dish_id:
                # A fixture with the cooked dish already in hand needs no raw
                # reservation; it can be served directly to this customer.
                reserved = {}
                reservation_state = "released"
            else:
                reserved = deepcopy(self.menu[dish_id]["recipe"])
                reservation_state = "reserved"
            if reservation_state == "reserved" and reserved != self.menu[dish_id]["recipe"]:
                raise BadInput(f"customers.{c['id']}.reserved phải bằng đúng recipe của dish_id")
            c["reserved"] = reserved
            self._reservation_state[c["id"]] = reservation_state
            self.customers.append(c)
        reserved_totals = {}
        for customer in self.customers:
            if self._reservation_state[customer["id"]] != "reserved":
                continue
            for kind, amount in customer["reserved"].items():
                reserved_totals[kind] = reserved_totals.get(kind, 0) + amount
        if any(self.stock.get(kind, 0) < amount for kind, amount in reserved_totals.items()):
            raise BadInput("nguyên liệu giữ chỗ vượt kho")
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self.elapsed_ticks = 0

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
        reserved = {}
        for c in self.customers:
            for kind, amount in c.get("reserved", {}).items():
                reserved[kind] = reserved.get(kind, 0) + amount
        available = {}
        for kind, amount in self.stock.items():
            remaining = amount - reserved.get(kind, 0)
            if remaining > 0:
                available[kind] = remaining
        return {
            "player": {"pos": self.pos},
            "stock": {k: available[k] for k in sorted(available)},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.elapsed_ticks += 1
        events.extend(self._tick_customers())
        events.extend(self._tick_stoves())
        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())
        events.extend(self._spawn_customers())
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _available_stock(self):
        reserved = {}
        for c in self.customers:
            for kind, amount in c.get("reserved", {}).items():
                reserved[kind] = reserved.get(kind, 0) + amount
        return {kind: amount - reserved.get(kind, 0) for kind, amount in self.stock.items()
                if amount - reserved.get(kind, 0) > 0}

    def _has_recipe(self, recipe, available=None):
        available = self._available_stock() if available is None else available
        return all(available.get(kind, 0) >= amount for kind, amount in recipe.items())

    def _reserve_for_customer(self, customer):
        """Atomically reserve a complete recipe without changing physical stock."""
        customer_id = customer["id"]
        dish_id = customer.get("dish_id", customer.get("dish"))
        if dish_id not in self.menu:
            return False
        state = self._reservation_state.get(customer_id)
        recipe = dict(self.menu[dish_id]["recipe"])
        if state == "reserved":
            return customer.get("reserved", {}) == recipe
        if state in ("consumed", "released"):
            return False
        existing_reserved = customer.get("reserved", {})
        if existing_reserved and existing_reserved != recipe:
            return False
        if not self._has_recipe(recipe):
            return False
        customer["dish_id"] = dish_id
        customer["reserved"] = recipe
        self._reservation_state[customer_id] = "reserved"
        return True

    def _consume_reservation(self, customer_id):
        """Debit physical stock once and transfer a reserved recipe to cooking."""
        if self._reservation_state.get(customer_id) != "reserved":
            return False
        customer = next((c for c in self.customers if c["id"] == customer_id), None)
        if customer is None:
            return False
        reserved = dict(customer.get("reserved", {}))
        recipe = self.menu[customer["dish_id"]]["recipe"]
        if reserved != recipe or any(self.stock.get(kind, 0) < amount for kind, amount in reserved.items()):
            return False
        for kind, amount in reserved.items():
            self.stock[kind] -= amount
            if self.stock[kind] == 0:
                del self.stock[kind]
        customer["reserved"] = {}
        self._reservation_state[customer_id] = "consumed"
        return True

    def _release_reservation(self, customer_id):
        """Release an unconsumed reservation once; never add stock back."""
        if self._reservation_state.get(customer_id) != "reserved":
            return {}
        customer = next((c for c in self.customers if c["id"] == customer_id), None)
        if customer is None:
            return {}
        released = dict(customer.get("reserved", {}))
        customer["reserved"] = {}
        self._reservation_state[customer_id] = "released"
        return released

    def _can_accept_order(self):
        occupied = {c["table_id"] for c in self.customers}
        if not any(tb["id"] not in occupied for tb in self.tables):
            return False
        available = self._available_stock()
        return any(self._has_recipe(d["recipe"], available) for d in self.menu.values())

    def _has_active_work(self):
        return bool(self.customers or self.hand is not None or
                    any(stove["state"] != "idle" for stove in self.stoves))

    def _spawn_customers(self):
        events = []
        if not self.random_customers:
            return events
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * self.tick_hz))
        if self.elapsed_ticks < first:
            return events
        if (self.elapsed_ticks - first) % interval != 0:
            return events
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return events
        available = self._available_stock()
        dishes = [dish_id for dish_id in sorted(self.menu)
                  if self._has_recipe(self.menu[dish_id]["recipe"], available)]
        if not dishes:
            return events
        dish_id = self.rng.get("customer_dish").choice(dishes)
        tb = free_tables[0]
        c = {"id": self.ids.new("C"), "table_id": tb["id"], "dish_id": dish_id,
             "state": "waiting",
             "patience_ticks_left": int(round(self.t["patience_s"] * self.tick_hz)),
             "eat_ticks_left": int(round(self.t["eat_s"] * self.tick_hz)),
             "reserved": {}}
        if not self._reserve_for_customer(c):
            return events
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": tb["id"],
                                             "dish_id": dish_id}))
        return events

    def _tick_customers(self):
        events = []
        remaining = []
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, int(c.get("eat_ticks_left", 0)) - 1)
                if c["eat_ticks_left"] <= 0:
                    dish_id = c["dish_id"]
                    menu = self.menu[dish_id]
                    price = int(menu["price"])
                    p_max = c.get("patience_max_ticks", self.t["patience_s"] * self.tick_hz)
                    patience_ratio = c.get(
                        "patience_ratio_served",
                        c["patience_ticks_left"] / p_max if p_max > 0 else 1.0,
                    )
                    tip = 0
                    if patience_ratio >= self.t["tip_min_patience_ratio"]:
                        tip = int(round(price * self.t["tip_rate"]))
                        if tip > 0 or self.t.get("tip_reputation", 0) > 0:
                            self.reputation = min(float(self.t["reputation_max"]),
                                                  round(self.reputation + float(self.t["tip_reputation"]), 3))
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "dish_id": dish_id, "dish": dish_id, "price": price,
                                            "money": price, "tip": tip, "reputation": self.reputation,
                                            "patience_ratio": patience_ratio}))
                    continue
            elif c["state"] in ("waiting", "ordered"):
                c["patience_ticks_left"] = max(0, int(c.get("patience_ticks_left", 0)) - 1)
                c["patience_ticks"] = c["patience_ticks_left"]
                if c["patience_ticks_left"] <= 0:
                    self._release_reservation(c["id"])
                    self.reputation = max(float(self.t["reputation_min"]),
                                          self.reputation + float(self.t["left_reputation_delta"]))
                    events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                     "dish_id": c["dish_id"]}))
                    continue
            remaining.append(c)
        self.customers = remaining
        return events

    def _tick_stoves(self):
        events = []
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, int(s.get("cook_ticks_left", 0)) - 1)
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = int(s.get("ready_ticks", 0))
                    s["cook_ticks_left"] = 0
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"], "dish": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] = int(s.get("ready_ticks", 0)) + 1
        return events

    def _nearest_interaction(self):
        if not hasattr(self, "_interact_radius"):
            pass
        candidates = []
        for s in sort_by_id(self.stoves):
            dist = ((self.pos[0] - s["pos"][0]) ** 2 + (self.pos[1] - s["pos"][1]) ** 2) ** 0.5
            if dist <= self.t["interact_radius"]:
                candidates.append((dist, 0, s["id"], "stove", s))
        for tb in sort_by_id(self.tables):
            dist = ((self.pos[0] - tb["pos"][0]) ** 2 + (self.pos[1] - tb["pos"][1]) ** 2) ** 0.5
            if dist <= self.t["interact_radius"]:
                candidates.append((dist, 1, tb["id"], "table", tb))
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item[0], item[1], item[2]))[3:]

    def _interact(self):
        events = []
        target = self._nearest_interaction()
        if not target:
            return events
        kind, obj = target
        if kind == "stove":
            if obj["state"] == "idle" and self.hand is None:
                waiting = [c for c in sort_by_id(self.customers)
                           if c["state"] == "waiting"
                           and self._has_reserved_recipe(c)]
                if waiting:
                    c = waiting[0]
                    dish_id = c["dish_id"]
                    if not self._consume_reservation(c["id"]):
                        return events
                    c["state"] = "ordered"
                    obj["state"] = "cooking"
                    obj["dish"] = dish_id
                    obj["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * self.tick_hz))
                    events.append(("cook_started", {"stove_id": obj["id"], "customer_id": c["id"],
                                                    "dish_id": dish_id, "dish": dish_id}))
            elif obj["state"] == "ready" and self.hand is None:
                dish_id = obj["dish"]
                obj["state"] = "idle"
                obj["dish"] = None
                obj["cook_ticks_left"] = 0
                obj["ready_ticks"] = 0
                self.hand = dish_id
                events.append(("dish_picked", {"stove_id": obj["id"], "dish_id": dish_id, "dish": dish_id}))
        else:
            if self.hand is not None:
                for c in sort_by_id(self.customers):
                    if c["table_id"] == obj["id"] and c["state"] in ("waiting", "ordered"):
                        if c["dish_id"] != self.hand:
                            continue
                        c["state"] = "eating"
                        c["eat_ticks_left"] = int(round(self.t["eat_s"] * self.tick_hz))
                        p_left = c.get("patience_ticks_left", c.get("patience_ticks", 0))
                        p_max = c.get("patience_max_ticks", int(round(self.t["patience_s"] * self.tick_hz)))
                        c["patience_ratio_served"] = p_left / p_max if p_max > 0 else 1.0
                        dish_id = self.hand
                        self.hand = None
                        events.append(("served", {"customer_id": c["id"], "table_id": obj["id"],
                                                  "dish_id": dish_id, "dish": dish_id}))
                        break
        return events

    def _has_reserved_recipe(self, customer):
        dish_id = customer.get("dish_id")
        if dish_id not in self.menu:
            return False
        recipe = self.menu[dish_id]["recipe"]
        reserved = customer.get("reserved", {})
        return all(reserved.get(kind, 0) >= amount for kind, amount in recipe.items())

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
