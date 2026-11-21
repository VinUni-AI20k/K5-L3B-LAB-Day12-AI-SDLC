"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phase 1 (PRD-0 mục F, Quán):
  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
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
        self.customers = []
        for source in sort_by_id(scenario.get("customers", [])):
            c = dict(source)
            dish_id = c.get("dish_id", c.get("dish"))
            reserved = dict(c.get("reserved", {}))
            if "dish_id" not in c:
                c["dish_id"] = dish_id
            c["state"] = c.get("state", "waiting")
            if "patience_ticks_left" in c:
                patience = int(c["patience_ticks_left"])
            elif "patience_ticks" in c:
                patience = int(c["patience_ticks"])
            elif "patience_s" in c:
                patience = int(round(float(c["patience_s"]) * TICK))
            else:
                patience = int(round(t["patience_s"] * TICK))
            c["patience_ticks_left"] = patience
            eat_ticks = c.get("eat_ticks_left")
            if eat_ticks is None:
                eat_ticks = int(round(t["eat_s"] * TICK))
            c["eat_ticks_left"] = int(eat_ticks)
            if not reserved and dish_id in self.menu:
                reserved = dict(self.menu[dish_id]["recipe"])
            c["reserved"] = reserved
            self.customers.append(c)
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
        return {kind: amount - reserved.get(kind, 0) for kind, amount in self.stock.items()}

    def _has_recipe(self, recipe, available=None):
        available = self._available_stock() if available is None else available
        return all(available.get(kind, 0) >= amount for kind, amount in recipe.items())

    def _spawn_customers(self):
        events = []
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if self.elapsed_ticks < first:
            return events
        if (self.elapsed_ticks - first) % interval != 0:
            return events
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            events.append(("no_dish", {"reason": "no_free_table"}))
            return events
        available = self._available_stock()
        dishes = [dish_id for dish_id in sorted(self.menu)
                  if self._has_recipe(self.menu[dish_id]["recipe"], available)]
        if not dishes:
            events.append(("no_dish", {"reason": "insufficient_ingredients"}))
            return events
        dish_id = self.rng.get("customer_dish").choice(dishes)
        tb = free_tables[0]
        c = {"id": self.ids.new("C"), "table_id": tb["id"], "dish_id": dish_id,
             "state": "waiting",
             "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
             "eat_ticks_left": int(round(self.t["eat_s"] * TICK)),
             "reserved": dict(self.menu[dish_id]["recipe"])}
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
                    patience_ratio = c["patience_ticks_left"] / (self.t["patience_s"] * TICK)
                    tip = 0
                    if patience_ratio >= self.t["tip_min_patience_ratio"]:
                        tip = int(round(price * self.t["tip_rate"]))
                        if tip > 0:
                            self.reputation = min(float(self.t["reputation_max"]),
                                                  self.reputation + float(self.t["tip_reputation"]))
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "dish_id": dish_id, "price": price, "tip": tip,
                                            "patience_ratio": patience_ratio}))
                    continue
            elif c["state"] in ("waiting", "ordered"):
                c["patience_ticks_left"] = max(0, int(c.get("patience_ticks_left", 0)) - 1)
                if c["patience_ticks_left"] <= 0:
                    for kind, amount in c.get("reserved", {}).items():
                        c["reserved"][kind] = max(0, c["reserved"][kind] - amount)
                    c["reserved"] = {}
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
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"]}))
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
                    recipe = self.menu[dish_id]["recipe"]
                    for item, amount in recipe.items():
                        self.stock[item] = max(0, self.stock.get(item, 0) - amount)
                        c["reserved"][item] = max(0, c["reserved"].get(item, 0) - amount)
                    c["reserved"] = {k: v for k, v in c["reserved"].items() if v > 0}
                    c["state"] = "ordered"
                    obj["state"] = "cooking"
                    obj["dish"] = dish_id
                    obj["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
                    events.append(("cook_started", {"stove_id": obj["id"], "customer_id": c["id"],
                                                    "dish_id": dish_id}))
            elif obj["state"] == "ready" and self.hand is None:
                dish_id = obj["dish"]
                obj["state"] = "idle"
                obj["dish"] = None
                obj["cook_ticks_left"] = 0
                obj["ready_ticks"] = 0
                self.hand = dish_id
                events.append(("dish_picked", {"stove_id": obj["id"], "dish_id": dish_id}))
        else:
            if self.hand is not None:
                for c in sort_by_id(self.customers):
                    if c["table_id"] == obj["id"] and c["state"] in ("waiting", "ordered"):
                        if c["dish_id"] != self.hand:
                            continue
                        c["state"] = "eating"
                        c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                        dish_id = self.hand
                        self.hand = None
                        events.append(("served", {"customer_id": c["id"], "table_id": obj["id"],
                                                  "dish_id": dish_id}))
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
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
