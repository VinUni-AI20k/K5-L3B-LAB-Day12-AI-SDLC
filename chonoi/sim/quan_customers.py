"""M3 — Quán: Khách (PRD-0 mục D, E, F).

Tách khỏi quan.py để M3 (khách) và M4 (bếp/tiền) ít đụng nhau. Phạm vi:
  - dựng khách từ scenario (mặc định các trường, giữ chỗ nguyên liệu theo công thức);
  - kiên nhẫn / thời gian ăn đếm lùi, khách rời (hết kiên nhẫn / hết ca), trừ uy tín;
  - khách mới theo lịch, chọn món đủ nguyên liệu khả dụng, `customer_arrived` / `no_dish`.

Số liệu chỉ đọc từ tuning (self.t / self.menu); ngẫu nhiên chỉ qua self.rng (Streams).
Móc nối với M4: `_pay_customer` và `_release_order` dưới đây là bản tối thiểu để vòng đời khách chạy
được; M4 có thể thay bằng bản đầy đủ (cùng chữ ký) mà không phải sửa phần còn lại.
"""

from ..errors import BadInput
from ..ids import sort_by_id

CUSTOMER_FIELDS = ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                   "eat_ticks_left", "order_status", "reserved", "base_price", "tip")
CUSTOMER_PREFIX = "K"


class CustomerMixin:
    # ---- dựng khách ---------------------------------------------------------------------------
    def _init_customers(self, scenario, allowed_dishes=None):
        """`allowed_dishes`: tập id món khách được gọi khi tự sinh (chế độ `day` truyền món của kế hoạch ngày);
        None = dùng cả menu (quán chạy riêng). Khách dựng sẵn từ scenario không bị lọc."""
        self.allowed_dishes = self._check_allowed_dishes(allowed_dishes)
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self._patience_max = int(round(self.t["patience_s"] * 60))
        self.customers = [self._make_customer(c) for c in scenario.get("customers", [])]
        for c in self.customers:
            self.ids.reserve(c["id"])
        if self.item_mode:  # v1.2: đơn reserved thiếu `reserved` được cấp id cá thể theo order_tick rồi id bàn
            self._allocate_fixture_reservations([c for c in self.customers if c["reserved"] is None])

    def _make_customer(self, c):
        state = c.get("state", "waiting")
        status = c.get("order_status", "served" if state == "eating" else "reserved")
        if self.item_mode:  # v1.2: reserved là mảng id cá thể; None = chờ cấp từ kho
            if "reserved" in c:
                reserved = list(c["reserved"])
            else:
                reserved = None if status == "reserved" else []
        elif "reserved" in c:
            reserved = dict(c["reserved"])
        elif status == "reserved":
            reserved = dict(self.menu[c["dish_id"]]["recipe"])
        else:
            reserved = {}
        return {
            "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
            "order_tick": c.get("order_tick", 0), "state": state,
            "patience_ticks_left": c.get("patience_ticks_left", self._patience_max),
            "eat_ticks_left": c.get("eat_ticks_left", 0),
            "order_status": status, "reserved": reserved,
            "base_price": c.get("base_price"), "tip": c.get("tip"),
        }

    # ---- kho khả dụng ---------------------------------------------------------------------------
    def _available_stock(self):
        """Tồn vật lý trừ phần đã giữ chỗ của mọi đơn."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, q in c["reserved"].items():
                avail[k] = avail.get(k, 0) - q
        return avail

    def _check_allowed_dishes(self, allowed):
        if allowed is None:
            return None
        allowed = set(allowed)
        unknown = sorted(allowed - set(self.menu))
        if unknown:
            raise BadInput(f"allowed_dishes có món ngoài menu: {unknown}")
        return allowed

    def _cookable_dishes(self):
        """Món khách được gọi (lọc theo kế hoạch ngày trước) và đủ nguyên liệu khả dụng,
        sắp theo id (mã Unicode) để duyệt cố định. Không đếm số suất: gọi tiếp món đủ nguyên liệu
        vẫn được kể cả khi đã bán đủ số suất dự kiến."""
        pool = sorted(self.menu if self.allowed_dishes is None else self.allowed_dishes)
        if self.item_mode:
            return self._cookable_items_dishes(pool)
        avail = self._available_stock()
        return [d for d in pool
                if all(avail.get(k, 0) >= q for k, q in self.menu[d]["recipe"].items())]

    # ---- snapshot ---------------------------------------------------------------------------------
    def _customers_snapshot(self):
        out = []
        for c in sort_by_id(self.customers):
            row = {k: c[k] for k in CUSTOMER_FIELDS}
            if isinstance(row["reserved"], dict):
                row["reserved"] = {k: row["reserved"][k] for k in sorted(row["reserved"])}
            else:
                row["reserved"] = list(row["reserved"])  # v1.2: mảng id cá thể (đã sắp theo id)
            out.append(row)
        return out

    # ---- đầu bước: đếm lùi ------------------------------------------------------------------------
    def _tick_customer_timers(self):
        """Giảm thời gian ăn của khách đang ăn, kiên nhẫn của khách đang chờ (không âm)."""
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    # ---- sau interact: ăn xong / rời ---------------------------------------------------------------
    def _resolve_customers(self, events, closing):
        """Theo id bàn: ăn xong trả tiền rồi rời; còn giờ thì khách chờ hết kiên nhẫn rời (trừ uy tín);
        hết ca thì khách còn ăn trả ngay, khách còn chờ rời với reason 'closing' (không trừ uy tín)."""
        for c in sorted(self.customers, key=lambda x: self._table_order(x["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] <= 0:
                    self._pay_customer(c, "finished_eating", events)
                elif closing:
                    self._pay_customer(c, "closing", events)
            elif closing:
                self._customer_leaves(c, "closing", events, penalty=False)
            elif c["patience_ticks_left"] <= 0:
                self._customer_leaves(c, "patience", events, penalty=True)

    def _table_order(self, table_id):
        ids = [t["id"] for t in self.tables]
        return ids.index(table_id) if table_id in ids else len(ids)

    def _customer_leaves(self, c, reason, events, penalty):
        if penalty:
            self.reputation = self._clamp_rep(self.reputation + self.t["left_reputation_delta"])
        self._release_order(c["id"])
        self.customers.remove(c)  # phần giữ chỗ nằm trong khách nên được nhả theo
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                         "reason": reason, "reputation": self.reputation}))

    def _clamp_rep(self, v):
        return max(self.t["reputation_min"], min(self.t["reputation_max"], v))

    # ---- móc nối M4 (bản tối thiểu, M4 có thể thay) -----------------------------------------------
    def _pay_customer(self, c, reason, events):
        base, tip = c["base_price"] or 0, c["tip"] or 0
        amount = base + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self.reputation = self._clamp_rep(self.reputation + self.t["tip_reputation"])
        self.customers.remove(c)
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": base,
                                "tip": tip, "amount": amount, "reason": reason}))

    def _release_order(self, order_id):
        """Bỏ món của đơn đang nấu / ready / trên tay (nguyên liệu đã dùng không hoàn lại)."""
        for s in self.stoves:
            d = s.get("dish")
            if d and d["order_id"] == order_id:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand["order_id"] == order_id:
            self.hand = None

    # ---- cuối bước: khách mới theo lịch -----------------------------------------------------------
    def _spawn_customer(self, events):
        if not self.random_customers:
            return
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * 60))
        if self.phase_tick < first or (self.phase_tick - first) % interval != 0:
            return
        taken = {c["table_id"] for c in self.customers}
        free = [t for t in self.tables if t["id"] not in taken]
        if not free:
            return  # không còn bàn: bỏ lượt
        table_id = free[0]["id"]  # self.tables đã sắp theo id -> bàn trống id nhỏ nhất
        dishes = self._cookable_dishes()
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = dishes[self.rng.get("customer_dish").randrange(len(dishes))]
        reserved = (self._try_reserve(self.menu[dish_id]["recipe"]) if self.item_mode
                    else dict(self.menu[dish_id]["recipe"]))
        cid = self.ids.new(CUSTOMER_PREFIX)
        self.customers.append({
            "id": cid, "table_id": table_id, "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self._patience_max, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": reserved,
            "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table_id, "dish_id": dish_id}))
