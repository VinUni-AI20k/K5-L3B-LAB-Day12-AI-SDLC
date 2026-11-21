"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  Lát 3 (C): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
             bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


def _ticks(seconds):
    return int(round(seconds * 60))


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
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._customer_from_scenario(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._check_reserved_fits_stock()
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

    # ---- Lát 3: dữ liệu khách -------------------------------------------------

    def _customer_from_scenario(self, c):
        """Khách dựng sẵn: điền mặc định theo hợp đồng; đơn reserved thiếu `reserved` thì cấp theo công thức."""
        dish_id = c.get("dish_id")
        status = c.get("order_status", "reserved")
        if "reserved" in c:
            reserved = dict(c["reserved"])
        elif status == "reserved" and dish_id in self.menu:
            reserved = dict(self.menu[dish_id]["recipe"])
        else:
            reserved = {}
        price = self.menu[dish_id]["price"] if dish_id in self.menu else 0
        return {
            "id": c["id"],
            "table_id": c["table_id"],
            "dish_id": dish_id,
            "order_tick": c.get("order_tick", 0),
            "state": c.get("state", "waiting"),
            "patience_ticks_left": c.get("patience_ticks_left", _ticks(self.t["patience_s"])),
            "eat_ticks_left": c.get("eat_ticks_left", 0),
            "order_status": status,
            "reserved": reserved,
            "base_price": c.get("base_price", price),
            "tip": c.get("tip", 0),
        }

    def _reserved_total(self):
        total = {}
        for c in self.customers:
            for k, n in c["reserved"].items():
                total[k] = total.get(k, 0) + n
        return total

    def _check_reserved_fits_stock(self):
        # Phải kiểm ở đây vì kho có thể đến từ --inventory (scenario.py không thấy file kho).
        from ..errors import BadInput
        for k, n in self._reserved_total().items():
            if n > self.stock.get(k, 0):
                raise BadInput(f"khách giữ {n} {k} nhưng kho chỉ có {self.stock.get(k, 0)}")

    def available_stock(self):
        """Kho khả dụng = tồn kho trừ phần các khách đang giữ."""
        held = self._reserved_total()
        return {k: self.stock[k] - held.get(k, 0) for k in self.stock}

    # ---- snapshot / step ------------------------------------------------------

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
        self._tick_timers()                 # C (kiên nhẫn) + D (nấu, ăn)
        self._stoves_ready(events)          # D
        self._move(inp)
        self._interact(inp, events)         # D
        self._settle_customers(events)      # C (bỏ đi) + D (trả tiền); chốt hết ca
        self._spawn_customer(events)        # C
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _tick_timers(self):
        # C: kiên nhẫn giảm 1 mỗi bước cho khách đang chờ (khách mới sinh cuối bước trước nên giảm từ bước này).
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # TODO(D): cook_ticks_left, eat_ticks_left, ready_ticks.

    def _stoves_ready(self, events):
        pass  # TODO(D)

    def _interact(self, inp, events):
        pass  # TODO(D)

    def _settle_customers(self, events):
        # Hết ca: khách đang ăn trả tiền trước (D), rồi khách đang chờ rời với closing (C), rồi quan_end.
        self._pay_customers(events)         # D
        closing = self.time_left_ticks <= 0
        for c in self._by_table([c for c in self.customers if c["state"] == "waiting"]):
            if closing:
                self._customer_leaves(c, "closing", events)
            elif c["patience_ticks_left"] <= 0:
                lo, hi = self.t["reputation_min"], self.t["reputation_max"]
                self.reputation = min(hi, max(lo, self.reputation + self.t["left_reputation_delta"]))
                self._customer_leaves(c, "patience", events)

    def _pay_customers(self, events):
        pass  # TODO(D): khách eating ăn xong (hoặc hết ca, reason closing) -> paid rồi rời bàn.

    def _drop_order(self, order_id):
        pass  # TODO(D): bỏ món của đơn order_id trên bếp hoặc trên tay.

    def _by_table(self, customers):
        order = [tb["id"] for tb in self.tables]  # self.tables đã sort_by_id
        return sorted(customers, key=lambda c: order.index(c["table_id"]))

    def _customer_leaves(self, c, reason, events):
        """Khách rời: nhả `reserved` (nằm trên chính khách, bỏ khách là nhả), D dọn món của đơn."""
        self.customers.remove(c)
        self._drop_order(c["id"])
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                         "reason": reason, "reputation": self.reputation}))

    def _spawn_customer(self, events):
        if not self.random_customers or self.time_left_ticks <= 0:
            return
        first = self.t["first_customer_tick"]
        every = _ticks(self.t["customer_interval_s"])
        pt = self.phase_tick
        if pt < first or (pt - first) % every != 0:
            return
        occupied = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in occupied]  # self.tables đã sort_by_id
        if not free:
            return
        avail = self.available_stock()
        dishes = [d for d in sorted(self.menu)
                  if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = dishes[self.rng.get("customers").randrange(len(dishes))]
        dish = self.menu[dish_id]
        c = {
            "id": self.ids.new("C"),
            "table_id": free[0]["id"],
            "dish_id": dish_id,
            "order_tick": pt,
            "state": "waiting",
            "patience_ticks_left": _ticks(self.t["patience_s"]),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": dict(dish["recipe"]),
            "base_price": dish["price"],
            "tip": 0,
        }
        self.customers.append(c)
        events.append(("customer_arrived", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": dish_id}))

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
