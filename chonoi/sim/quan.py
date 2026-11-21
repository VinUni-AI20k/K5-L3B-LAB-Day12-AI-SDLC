"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  Lát 3 (minhtriet061203) — ĐÃ LÀM: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu,
                     kiên nhẫn, bỏ đi (customer_left patience/closing), no_dish, khách dựng từ scenario.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid finished_eating/closing), boa, uy tín.

Cấu trúc khách: PRD-0 mục D + docs/contracts/README.md mục 4 (order_id = id khách):
  {"id","table_id","dish_id","order_tick","state","patience_ticks_left","eat_ticks_left",
   "order_status","reserved","base_price","tip"}
  state: waiting -> eating; order_status: reserved (lát 3) -> assigned -> served (lát 4); unfulfillable (fixture).
Kho khả dụng = tồn (`stock`) − tổng `reserved` của mọi khách (xem `available()`).
"""

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
RNG_CUSTOMERS = "customers"  # luồng RNG riêng cho việc chọn món (clarify G1)
CUSTOMER_FIELDS = ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                   "order_status", "reserved", "base_price", "tip")


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
        # khách dựng sẵn từ scenario: giữ id, suy ra giữ chỗ
        fixture = scenario.get("customers", [])
        for c in fixture:
            ids.reserve(c["id"])
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

    def _new_customer(self, cid, table_id, dish_id, order_tick):
        return {"id": cid, "table_id": table_id, "dish_id": dish_id, "order_tick": order_tick,
                "state": "waiting", "patience_ticks_left": self.patience_ticks, "eat_ticks_left": 0,
                "order_status": "reserved", "reserved": dict(self.menu[dish_id]["recipe"]),
                "base_price": 0, "tip": 0}

    def _customer_from_fixture(self, c):
        cust = self._new_customer(c["id"], c["table_id"], c["dish_id"], c.get("order_tick", 0))
        if c.get("state", "waiting") == "eating":
            cust.update(state="eating", order_status="served")
        for k in ("patience_ticks_left", "eat_ticks_left", "order_status", "base_price", "tip"):
            if k in c:
                cust[k] = c[k]
        if cust["order_status"] != "reserved":
            cust["reserved"] = {}
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

    def _release(self, c):
        """Hợp đồng mục 4: khách rời -> nhả phần giữ, bỏ món của đơn ở bếp (về idle) hoặc trên tay."""
        c["reserved"] = {}
        for s in self.stoves:
            if isinstance(s.get("dish"), dict) and s["dish"].get("order_id") == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if isinstance(self.hand, dict) and self.hand.get("order_id") == c["id"]:
            self.hand = None
        self.customers = [x for x in self.customers if x["id"] != c["id"]]

    def _customer_left(self, c, reason, events, rep_delta=0.0):
        """Khách rời: _release, đổi uy tín (kẹp), customer_left mang uy tín SAU khi đổi (clarify #3)."""
        self._release(c)
        if rep_delta:
            self._add_reputation(rep_delta)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
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
            "customers": [{k: ({i: c[k][i] for i in sorted(c[k])} if k == "reserved" else c[k])
                           for k in CUSTOMER_FIELDS} for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        """Thứ tự theo PRD-0 mục F (Quán), đánh số 1–5 như PRD."""
        events = []
        # 1. đồng hồ, timer ca, nấu, ăn, kiên nhẫn
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # TODO(nhóm, lát 4): giảm cook_ticks_left / eat_ticks_left; tăng ready_ticks cho món ready từ đầu bước.
        self._tick_patience()
        # 2. TODO(nhóm, lát 4): xét bếp theo id, món nấu xong -> ready (ready_ticks = 0), dish_ready.
        # 3. di chuyển rồi tối đa MỘT interact
        self._move(inp)
        # TODO(nhóm, lát 4): interact chọn theo (khoảng cách, bếp trước bàn, id).
        # 4. theo id bàn: ăn xong trả tiền / hết kiên nhẫn / hết ca; dọn xong -> quan_end
        self._settle_tables(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. còn giờ: lượt khách mới
        self._spawn_customer(events)
        return events

    def _tick_patience(self):
        """Bước 1: khách đang chờ mất 1 tick kiên nhẫn (không âm). Rời bàn xét ở bước 4."""
        for c in self.customers:
            if c["state"] == "waiting":  # khách đang ăn không giảm kiên nhẫn (clarify #9)
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _settle_tables(self, events):
        """Bước 4, theo id bàn. Phục vụ đúng tick kiên nhẫn về 0 (bước 3) thì khách đã eating, không rời."""
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
            if c["state"] == "eating":
                # TODO(nhóm, lát 4): eat_ticks_left == 0 -> paid finished_eating; hết ca -> paid closing; rời bàn.
                continue
            if closing:
                self._customer_left(c, "closing", events)  # không trừ uy tín
            elif c["patience_ticks_left"] == 0:
                self._customer_left(c, "patience", events, rep_delta=self.t["left_reputation_delta"])

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
            events.append(("no_dish", {}))
            return
        dish_id = options[self.rng.get(RNG_CUSTOMERS).randrange(len(options))]
        c = self._new_customer(self.ids.new("C"), table["id"], dish_id, self.phase_tick)
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
