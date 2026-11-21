"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  Lát 3 (minhtriet061203) — ĐÃ LÀM: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu,
                     kiên nhẫn, bỏ đi (customer_left), no_dish, vòng đời khách, khách dựng từ scenario.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).

Cấu trúc khách (snapshot `customers[]`, chốt giữa lát 3 và lát 4):
  id, table_id, state ("waiting" | "eating"), order_id, dish_id, base_price,
  order_state ("reserved" -> "cooking" -> "ready" -> "carried"), patience_ticks_left,
  reserved ({kind: n} — nguyên liệu đang giữ; rỗng khi bếp đã tiêu), arrived_tick.
  Khách "eating" có thêm eat_ticks_left, price, tip (lát 4 điền khi served).
Kho khả dụng = tồn (`stock`) − tổng `reserved` của mọi khách (xem `available()`).
"""

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
RNG_CUSTOMER = "quan_customer"  # luồng RNG riêng cho việc chọn món của khách


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
        # lịch khách (theo phase_tick, đếm từ 0 ở đầu ca)
        self.phase_tick = 0
        self.first_customer_tick = int(t["first_customer_tick"])
        self.customer_interval_ticks = max(1, int(round(t["customer_interval_s"] * 60)))
        self.patience_ticks = int(round(t["patience_s"] * 60))
        self.random_customers = scenario.get("random_customers", True)
        # khách dựng sẵn từ scenario: giữ id, suy ra đơn + giữ chỗ
        fixture = scenario.get("customers", [])
        for c in fixture:
            ids.reserve(c["id"])
            if c.get("order_id"):
                ids.reserve(c["order_id"])
        self.customers = [self._customer_from_fixture(c) for c in sort_by_id(fixture)]
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

    # ---------- khách: dựng từ scenario ----------

    def _customer_from_fixture(self, c):
        dish = self.menu[c["dish_id"]]
        state = c.get("state", "waiting")
        order_state = c.get("order_state", "reserved" if state == "waiting" else "served")
        reserved = dict(dish["recipe"]) if order_state == "reserved" else {}
        cust = {
            "id": c["id"],
            "table_id": c["table_id"],
            "state": state,
            "order_id": c.get("order_id") or self.ids.new("O"),
            "dish_id": c["dish_id"],
            "base_price": dish["price"],
            "order_state": order_state,
            "patience_ticks_left": c.get("patience_ticks_left", self.patience_ticks),
            "reserved": reserved,
            "arrived_tick": c.get("arrived_tick", 0),
        }
        for k in ("eat_ticks_left", "price", "tip"):
            if k in c:
                cust[k] = c[k]
        return cust

    def _check_reserved_fits_stock(self):
        """Mâu thuẫn: khách giữ chỗ nhiều hơn tồn kho (kho có thể đến từ --inventory) -> mã 2."""
        from ..errors import BadInput
        need = self._reserved_total()
        for k in sorted(need):
            if need[k] > self.stock.get(k, 0):
                raise BadInput(f"khách giữ chỗ {need[k]} {k} nhưng kho chỉ có {self.stock.get(k, 0)}")

    # ---------- kho khả dụng / giữ chỗ ----------

    def _reserved_total(self) -> dict:
        tot = {}
        for c in self.customers:
            for k, n in c["reserved"].items():
                tot[k] = tot.get(k, 0) + n
        return tot

    def available(self) -> dict:
        """Kho khả dụng = tồn − đang giữ (không âm)."""
        res = self._reserved_total()
        return {k: max(0, self.stock.get(k, 0) - res.get(k, 0)) for k in set(self.stock) | set(res)}

    def _cookable_dishes(self) -> list:
        avail = self.available()
        return [d for d in sorted(self.menu)
                if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]

    # ---------- uy tín / rời quán (dùng chung với lát 4) ----------

    def _add_reputation(self, delta):
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        self.reputation = round(min(hi, max(lo, self.reputation + delta)), 6)

    def _drop_order(self, order_id):
        """Bỏ món của đơn: bếp đang nấu/đã chín món đó về idle, tay đang bưng món đó thì bỏ."""
        for s in self.stoves:
            if s.get("order_id") == order_id:
                s.update(state="idle", dish=None, order_id=None, cook_ticks_left=0, ready_ticks=0)
        if isinstance(self.hand, dict) and self.hand.get("order_id") == order_id:
            self.hand = None

    def _remove_customer(self, c, reason, events, rep_delta=0.0):
        """Khách rời bàn: nhả giữ chỗ, bỏ món của đơn, phát customer_left, đổi uy tín."""
        self.customers = [x for x in self.customers if x["id"] != c["id"]]
        self._drop_order(c["order_id"])
        if rep_delta:
            self._add_reputation(rep_delta)
        events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                         "order_id": c["order_id"], "reason": reason,
                                         "reputation": self.reputation}))

    # ---------- bước ----------

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [dict(c, reserved={k: c["reserved"][k] for k in sorted(c["reserved"])})
                          for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_patience(events)
        # TODO(nhóm, lát 4): nấu / ăn; bếp chín -> ready.
        self._move(inp)
        # TODO(nhóm, lát 4): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        if self.time_left_ticks > 0:
            self._spawn_customer(events)
        if self.time_left_ticks <= 0:
            # TODO(nhóm, lát 4): khách đang ăn trả ngay (closing), khách chờ rời không trừ uy tín.
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _tick_patience(self, events):
        """Khách đang chờ mất 1 tick kiên nhẫn; về 0 -> customer_left patience, uy tín giảm."""
        for c in sort_by_id(self.customers):
            if c["state"] != "waiting":
                continue
            c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            if c["patience_ticks_left"] == 0:
                self._remove_customer(c, "patience", events, rep_delta=self.t["left_reputation_delta"])

    def _is_arrival_tick(self) -> bool:
        k = self.phase_tick - self.first_customer_tick
        return k >= 0 and k % self.customer_interval_ticks == 0

    def _spawn_customer(self, events):
        """Đúng lịch: bàn trống id nhỏ nhất; không bàn -> bỏ lượt; không món nấu được -> no_dish."""
        if not self.random_customers or not self._is_arrival_tick():
            return
        occupied = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in occupied]  # self.tables đã sort_by_id
        if not free:
            return
        table = free[0]
        options = self._cookable_dishes()
        if not options:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish_id = options[self.rng.get(RNG_CUSTOMER).randrange(len(options))]
        dish = self.menu[dish_id]
        c = {
            "id": self.ids.new("C"),
            "table_id": table["id"],
            "state": "waiting",
            "order_id": self.ids.new("O"),
            "dish_id": dish_id,
            "base_price": dish["price"],
            "order_state": "reserved",
            "patience_ticks_left": self.patience_ticks,
            "reserved": dict(dish["recipe"]),
            "arrived_tick": self.phase_tick,
        }
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "order_id": c["order_id"], "dish_id": dish_id,
                                            "base_price": c["base_price"],
                                            "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"])}}))

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
