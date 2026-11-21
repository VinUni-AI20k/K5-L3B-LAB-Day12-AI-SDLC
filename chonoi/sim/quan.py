"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Theo PRD-0 (mục D, E, F "Quán"):
  Lát 3 (TV2, ĐÃ LÀM): khách đến theo lịch phase_tick, chọn món đều theo seed, giữ chỗ nguyên liệu,
        kiên nhẫn, rời bàn (customer_left: patience / closing), no_dish, khách dựng sẵn từ scenario.
  TODO(nhóm, lát 4 — TV3): nấu / bếp ready / interact (cook_started, dish_ready, dish_picked, served),
        ăn xong trả tiền (paid: finished_eating / closing), boa, tiền.

Khách (mục D): {id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left,
                order_status, reserved, base_price, tip}
  state: waiting | eating · order_status: reserved | assigned | unfulfillable | served
  order_id của đơn = id khách. Payload món (bếp `dish`, `hand`) = {order_id, dish_id, base_price}.
Kho: `stock` là tồn VẬT LÝ, gồm cả phần giữ chỗ. Kho khả dụng = stock − Σ reserved (`available_stock`).
  Lát 4 khi bắt đầu nấu: trừ stock đúng phần giữ, đặt reserved = {}, order_status = "assigned".
"""

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
CUSTOMER_DISH_STREAM = "customer_dish"  # luồng RNG riêng cho việc khách chọn món


def to_ticks(seconds) -> int:
    return int(round(seconds * TICK))


def recipe_fits(recipe: dict, available: dict) -> bool:
    return all(available.get(k, 0) >= n for k, n in recipe.items())


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
        self.duration_ticks = to_ticks(t["duration_s"])
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration_ticks)
        self.phase_tick = 0  # lịch khách tính theo phase_tick kể cả khi rút ngắn ca (PRD-0 mục D)
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # --- Lát 3 (TV2): khách ---
        self.patience_max_ticks = to_ticks(t["patience_s"])
        self.customer_interval_ticks = to_ticks(t["customer_interval_s"])
        self.random_customers = scenario.get("random_customers", True)
        self.customers = [self._customer_from_scenario(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._check_reserved_within_stock()
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
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        """Một bước theo PRD-0 mục F "Quán"."""
        events = []
        # 1. đồng hồ, timer ca, nấu, ăn, kiên nhẫn
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # TODO(nhóm, lát 4 — TV3): giảm cook_ticks_left, eat_ticks_left; tăng ready_ticks CHỈ cho món đã ready ở đầu bước.
        self._tick_patience()
        # 2. TODO(nhóm, lát 4 — TV3): xét bếp theo id: nấu xong -> ready, ready_ticks = 0, dish_ready.
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        # TODO(nhóm, lát 4 — TV3): interact chọn theo (khoảng cách, bếp trước bàn, id): cook_started / dish_picked / served.
        # 4. thanh toán, rời bàn, hết ca
        closing = self.time_left_ticks <= 0
        self._settle_customers(events, closing)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách mới (chỉ khi còn giờ)
        self._spawn_customer(events)
        return events

    # --- Lát 3 (TV2): khách — hàm dùng chung cho lát 4 ------------------------------
    def available_stock(self) -> dict:
        """Kho khả dụng = tồn vật lý − tổng phần giữ của mọi khách."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, n in c["reserved"].items():
                avail[k] = avail.get(k, 0) - n
        return avail

    def add_reputation(self, delta):
        """Cộng uy tín, kẹp [reputation_min, reputation_max]. Lát 4 dùng cho boa (tip_reputation)."""
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"], self.reputation + delta))

    def remove_customer(self, c):
        """Khách rời bàn: nhả phần giữ thô (xóa khách là nhả), bỏ món của đơn đang nấu / ready / trên tay.
        Nguyên liệu đã dùng không hoàn lại. Lát 4 gọi sau khi `paid`."""
        self.customers = [x for x in self.customers if x["id"] != c["id"]]
        for s in self.stoves:
            if s.get("dish") and s["dish"].get("order_id") == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand.get("order_id") == c["id"]:
            self.hand = None

    # --- Lát 3 (TV2): nội bộ ---------------------------------------------------------
    def _recipe(self, dish_id) -> dict:
        r = self.menu[dish_id]["recipe"]
        return {k: r[k] for k in sorted(r)}

    def _customer_from_scenario(self, src) -> dict:
        """Mặc định (mục D): waiting, order_tick 0, kiên nhẫn đầy, order_status reserved.
        Đơn reserved thiếu `reserved` thì cấp theo công thức; đơn khác giữ rỗng."""
        status = src.get("order_status", "reserved")
        reserved = src.get("reserved", self._recipe(src["dish_id"]) if status == "reserved" else {})
        return {"id": src["id"], "table_id": src["table_id"], "dish_id": src["dish_id"],
                "order_tick": src.get("order_tick", 0), "state": src.get("state", "waiting"),
                "patience_ticks_left": src.get("patience_ticks_left", self.patience_max_ticks),
                "eat_ticks_left": src.get("eat_ticks_left", 0), "order_status": status,
                "reserved": {k: reserved[k] for k in sorted(reserved) if reserved[k] > 0},
                "base_price": src.get("base_price"), "tip": src.get("tip")}

    def _check_reserved_within_stock(self):
        """Giữ chỗ quá tồn -> mã 2 (kiểm ở đây vì kho có thể đến từ --inventory)."""
        short = {k: -v for k, v in self.available_stock().items() if v < 0}
        if short:
            raise BadInput(f"khách giữ chỗ quá tồn kho (thiếu {dict(sorted(short.items()))})")

    def _tick_patience(self):
        """Bước 1: khách waiting mất 1 kiên nhẫn (không âm). Việc rời bàn xét ở bước 4."""
        for c in self.customers:
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _settle_customers(self, events, closing):
        """Bước 4, theo id bàn: khách ăn xong trả tiền rồi rời; còn giờ thì khách waiting hết kiên nhẫn rời
        (uy tín + left_reputation_delta); hết ca thì khách waiting rời với closing, không trừ uy tín."""
        for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
            if c["state"] == "eating":
                # TODO(nhóm, lát 4 — TV3): eat_ticks_left == 0 -> paid(finished_eating); closing -> paid(closing).
                #   Cộng tiền, boa dương thì add_reputation(tip_reputation), rồi self.remove_customer(c).
                continue
            if closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] == 0:
                self.add_reputation(self.t["left_reputation_delta"])
                self._leave(c, "patience", events)

    def _leave(self, c, reason, events):
        self.remove_customer(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    def _free_table(self):
        occupied = {c["table_id"] for c in self.customers}
        return next((tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied), None)

    def _choose_dish(self):
        """Chọn đều theo seed trong các món đủ nguyên liệu khả dụng; duyệt id món theo mã Unicode."""
        avail = self.available_stock()
        cookable = [d for d in sorted(self.menu) if recipe_fits(self.menu[d]["recipe"], avail)]
        if not cookable:
            return None
        return cookable[self.rng.get(CUSTOMER_DISH_STREAM).randrange(len(cookable))]

    def _spawn_customer(self, events):
        """Bước 5: lượt khách ở phase_tick = first_customer_tick + n × customer_interval. Không còn bàn -> bỏ lượt.
        Bàn trống id nhỏ nhất. Không món đủ -> no_dish {}. Khách mới giữ đúng công thức, order_tick = phase_tick,
        kiên nhẫn đầy (bắt đầu giảm từ bước sau)."""
        if not self.random_customers:
            return
        k, first = self.phase_tick, self.t["first_customer_tick"]
        if k < first or (k - first) % self.customer_interval_ticks:
            return
        table = self._free_table()
        if table is None:
            return
        dish = self._choose_dish()
        if dish is None:
            events.append(("no_dish", {}))
            return
        c = {"id": self.ids.new("C"), "table_id": table["id"], "dish_id": dish, "order_tick": k,
             "state": "waiting", "patience_ticks_left": self.patience_max_ticks, "eat_ticks_left": 0,
             "order_status": "reserved", "reserved": self._recipe(dish), "base_price": None, "tip": None}
        self.customers.append(c)
        events.append(("customer_arrived", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": dish}))

    # --- đi lại ---------------------------------------------------------------------
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
