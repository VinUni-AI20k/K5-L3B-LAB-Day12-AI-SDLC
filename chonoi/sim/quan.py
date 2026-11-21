"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm B (PhamMinhDuc): hoàn thiện PRD-0 mục F — khách, bếp, bàn, tiền, uy tín.
"""

from ..ids import sort_by_id
from ..scenario import validate_quan_links
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
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self._duration_ticks = int(round(t["duration_s"] * 60))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        reserved = validate_quan_links(scenario, tuning, self.stock)
        self.customers = [dict(c, reserved=reserved[c["id"]]) for c in scenario.get("customers", [])]
        for c in self.customers:
            ids.reserve(c["id"])
            # điền mặc định còn thiếu
            c.setdefault("state", "waiting")
            c.setdefault("order_status", "reserved")
            c.setdefault("patience_ticks_left", int(round(t["patience_s"] * 60)))
            c.setdefault("eat_ticks_left", 0)
            c.setdefault("order_tick", 0)
            c.setdefault("base_price", self.menu[c["dish_id"]]["price"])
            c.setdefault("tip", 0)
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        # elapsed ticks: 0 at scenario start
        self._elapsed_ticks = self._duration_ticks - self.time_left_ticks
        # next customer spawn tick
        interval_ticks = int(round(t["customer_interval_s"] * 60))
        first = t["first_customer_tick"]
        if self._elapsed_ticks < first:
            self._next_customer_tick = first
        else:
            # already past first; compute next
            passed = self._elapsed_ticks - first
            cycles = passed // interval_ticks + 1
            self._next_customer_tick = first + cycles * interval_ticks

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
            "customers": sort_by_id([{k: c[k] for k in c if k != "reserved"} for c in self.customers]),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._elapsed_ticks += 1

        # --- giảm kiên nhẫn, xử lý khách bỏ đi ---
        t = self.t
        staying = []
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
                if c["patience_ticks_left"] <= 0:
                    events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"]}))
                    # trả lại nguyên liệu giữ chỗ
                    if c["order_status"] == "reserved":
                        for k, v in c.get("reserved", {}).items():
                            self.stock[k] = self.stock.get(k, 0) + v
                    self.reputation = max(t["reputation_min"],
                                          min(t["reputation_max"],
                                              self.reputation + t["left_reputation_delta"]))
                    continue
            staying.append(c)
        self.customers = staying

        # --- tick bếp đang nấu → chín ---
        for sv in self.stoves:
            if sv["state"] == "cooking":
                sv["cook_ticks_left"] -= 1
                if sv["cook_ticks_left"] <= 0:
                    sv["cook_ticks_left"] = 0
                    sv["state"] = "ready"
                    sv["ready_ticks"] += 1
                    events.append(("dish_ready", {"stove_id": sv["id"], "dish": sv["dish"]}))

        # --- tick ăn → trả tiền ---
        done_eating = []
        still_eating = []
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] <= 0:
                    done_eating.append(c)
                else:
                    still_eating.append(c)
            else:
                still_eating.append(c)
        # xử lý paid
        for c in done_eating:
            total = c["base_price"] + c["tip"]
            self.money += total
            self.earned += total
            self.shift_earned += total
            events.append(("paid", {"customer_id": c["id"], "amount": total,
                                    "base_price": c["base_price"], "tip": c["tip"]}))
        self.customers = still_eating

        # --- sinh khách mới ---
        while self._elapsed_ticks >= self._next_customer_tick:
            self._spawn_customer(events)
            self._next_customer_tick += int(round(t["customer_interval_s"] * 60))

        # --- di chuyển ---
        self._move(inp)

        # --- interact (tối đa 1) ---
        if inp.pressed("interact"):
            self._do_interact(events)

        # --- hết giờ ---
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _spawn_customer(self, events):
        t = self.t
        # tìm bàn trống
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in occupied]
        if not free_tables:
            return

        # chọn món nấu được
        reserved_counts = {}
        for c in self.customers:
            if c["order_status"] == "reserved":
                for k, v in c.get("reserved", {}).items():
                    reserved_counts[k] = reserved_counts.get(k, 0) + v
        cookable = []
        for dish_id, dish in self.menu.items():
            recipe = dish["recipe"]
            ok = True
            for ing, qty in recipe.items():
                available = self.stock.get(ing, 0) - reserved_counts.get(ing, 0)
                if available < qty:
                    ok = False
                    break
            if ok:
                cookable.append(dish_id)

        # tìm bàn theo id
        table = sort_by_id(free_tables)[0]

        if not cookable:
            cid = self.ids.new("C")
            events.append(("customer_arrived", {"customer_id": cid, "table_id": table["id"]}))
            events.append(("no_dish", {"customer_id": cid}))
            return

        rng = self.rng.get("customer_dish")
        dish_id = rng.choice(sorted(cookable))
        recipe = self.menu[dish_id]["recipe"]

        # giữ chỗ nguyên liệu
        for k, v in recipe.items():
            reserved_counts[k] = reserved_counts.get(k, 0) + v

        cid = self.ids.new("C")
        patience_ticks = int(round(t["patience_s"] * 60))
        c = {
            "id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
            "state": "waiting",
            "order_status": "reserved",
            "patience_ticks_left": patience_ticks,
            "eat_ticks_left": 0,
            "order_tick": self._elapsed_ticks,
            "base_price": self.menu[dish_id]["price"],
            "tip": 0,
            "reserved": dict(recipe),
        }
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    def _do_interact(self, events):
        t = self.t
        r = t["interact_radius"]
        px, pz = self.pos

        def dist2(obj):
            ox, oz = obj["pos"]
            return (px - ox) ** 2 + (pz - oz) ** 2

        # collect candidates: (dist2, type_priority[stove=0/table=1], id, obj, type)
        candidates = []
        for sv in self.stoves:
            d2 = dist2(sv)
            if d2 <= r * r:
                candidates.append((d2, 0, sv["id"], sv, "stove"))
        for tb in self.tables:
            d2 = dist2(tb)
            if d2 <= r * r:
                candidates.append((d2, 1, tb["id"], tb, "table"))

        if not candidates:
            return

        from ..ids import id_key
        candidates.sort(key=lambda x: (x[0], x[1], id_key(x[2])))
        _, _, _, obj, kind = candidates[0]

        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, sv, events):
        t = self.t
        if sv["state"] == "idle":
            # tìm đơn reserved theo order_tick rồi table_id
            waiting_orders = [c for c in self.customers if c["order_status"] == "reserved"]
            if not waiting_orders:
                return
            from ..ids import id_key
            waiting_orders.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
            c = waiting_orders[0]
            recipe = self.menu[c["dish_id"]]["recipe"]
            # trừ kho
            for k, v in recipe.items():
                self.stock[k] = self.stock.get(k, 0) - v
            # xoá reserved
            c["reserved"] = {}
            c["order_status"] = "assigned"
            cook_ticks = int(round(self.menu[c["dish_id"]]["cook_s"] * 60))
            dish_payload = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": c["base_price"]}
            sv["state"] = "cooking"
            sv["dish"] = dish_payload
            sv["cook_ticks_left"] = cook_ticks
            sv["ready_ticks"] = 0
            events.append(("cook_started", {"stove_id": sv["id"], "order_id": c["id"],
                                            "dish_id": c["dish_id"]}))
        elif sv["state"] == "ready":
            # nhặt món nếu tay trống
            carry = t.get("carry_limit", 1)
            if self.hand is None:
                self.hand = sv["dish"]
                sv["state"] = "idle"
                sv["dish"] = None
                sv["cook_ticks_left"] = 0
                sv["ready_ticks"] = 0
                events.append(("dish_picked", {"dish": self.hand}))

    def _interact_table(self, tb, events):
        t = self.t
        if self.hand is None:
            return
        # tìm khách tại bàn này chờ đúng món
        c = next((x for x in self.customers
                  if x["table_id"] == tb["id"] and x["state"] == "waiting"
                  and x["order_status"] == "assigned"
                  and x["dish_id"] == self.hand["dish_id"]
                  and x["id"] == self.hand["order_id"]), None)
        if c is None:
            return
        patience_full = int(round(t["patience_s"] * 60))
        patience_ratio = c["patience_ticks_left"] / patience_full if patience_full > 0 else 0
        tip = 0
        if patience_ratio >= t["tip_min_patience_ratio"]:
            tip = int(round(c["base_price"] * t["tip_rate"]))
            self.reputation = max(t["reputation_min"],
                                  min(t["reputation_max"], self.reputation + t["tip_reputation"]))
        c["tip"] = tip
        c["state"] = "eating"
        c["order_status"] = "served"
        c["eat_ticks_left"] = int(round(t["eat_s"] * 60))
        self.hand = None
        events.append(("served", {"customer_id": c["id"], "table_id": tb["id"],
                                   "dish_id": c["dish_id"], "tip": tip}))

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
