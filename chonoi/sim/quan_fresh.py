"""M3 — Phase 3 (Contract v1.2 "Mùa Nước Nổi"): kho quán dạng cá thể có độ tươi (Ticket03 mục 1).

Kho quán là mảng cá thể `{id, kind, fresh}`. Chế độ này tự bật khi kho đưa vào là MẢNG (file kho v1.2 hoặc
`scenario.quan.stock` dạng mảng); kho dạng object đếm (v1.0/v1.1) vẫn chạy như cũ, nên chuyển schema không làm
vỡ test Phase 1–2 trong lúc dev.

Biểu diễn chính xác: độ tươi lưu bằng đơn vị nguyên (`chonoi.freshness.FRESH_SCALE` = 240 đơn vị/điểm).
Kho quán hao 0.25/s = đúng 1 đơn vị/tick; ngưỡng ươn `fresh < 30` so `units < 7200` nên không sai số float.

Luật (Ticket03):
  - hao tươi cả hàng đang giữ chỗ; hàng ươn vẫn chiếm ô, không dùng nấu;
  - `spoiled {item_id, kind, location:"stock"}` đúng một lần khi đi từ >= 30 xuống < 30, nhiều cá thể thì theo id;
  - giữ chỗ theo id: mỗi loại trong công thức lấy các cá thể khả dụng TƯƠI NHẤT, hòa theo id;
  - phần giữ có cá thể vừa ươn: nhả toàn bộ phần giữ của đơn và thử giữ lại đúng một lần; các đơn bị ảnh hưởng
    xử lý theo (order_tick, id bàn); không đủ thì đơn chuyển `unfulfillable`, khách chờ tới hạn kiên nhẫn.

Móc nối cho M4 (nấu): `_consume_reserved(cust)` lấy khỏi kho đúng các id đang giữ của đơn; `stock_items_out()`
trả kho dưới dạng mảng `{id, kind, fresh}` để bàn giao (Shop / ngày kế).
"""

from ..freshness import decay_units_per_tick, from_units, to_units
from ..ids import id_key, sort_by_id


class FreshStockMixin:
    # ---- dựng kho -----------------------------------------------------------------------------
    def _init_stock(self, raw, tuning):
        """`raw`: object đếm (v1.0/v1.1) hoặc mảng cá thể (v1.2)."""
        self.item_mode = isinstance(raw, list)
        if not self.item_mode:
            self.stock = dict(raw)
            return
        f = tuning["freshness"]
        self._decay_units = decay_units_per_tick(f["quan_decay_per_s"], tuning.get("tick_hz", 60))
        self._spoil_units = to_units(f["spoiled_below"])
        self.stock = [{"id": it["id"], "kind": it["kind"], "units": to_units(it["fresh"])} for it in raw]

    # ---- tra cứu --------------------------------------------------------------------------------
    def _is_spoiled(self, item):
        return item["units"] < self._spoil_units

    def _held_ids(self):
        held = set()
        for c in self.customers:
            held.update(c["reserved"] or ())
        return held

    def _free_items(self):
        """Cá thể chưa ươn và chưa bị đơn nào giữ."""
        held = self._held_ids()
        return [it for it in self.stock if it["id"] not in held and not self._is_spoiled(it)]

    def _try_reserve(self, recipe):
        """Chọn id theo công thức: mỗi loại lấy các cá thể khả dụng tươi nhất, hòa theo id.
        Trả mảng id (sắp theo id) hoặc None nếu thiếu (không giữ một phần)."""
        free = self._free_items()
        chosen = []
        for kind in sorted(recipe):
            pool = sorted((it for it in free if it["kind"] == kind),
                          key=lambda it: (-it["units"], id_key(it["id"])))
            if len(pool) < recipe[kind]:
                return None
            chosen.extend(pool[:recipe[kind]])
        return [it["id"] for it in sort_by_id(chosen)]

    def _cookable_items_dishes(self, pool):
        """Các món trong `pool` còn đủ cá thể khả dụng (chưa ươn, chưa giữ)."""
        counts = {}
        for it in self._free_items():
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        return [d for d in pool
                if all(counts.get(k, 0) >= q for k, q in self.menu[d]["recipe"].items())]

    # ---- giữ chỗ cho khách dựng sẵn --------------------------------------------------------------
    def _allocate_fixture_reservations(self, pending):
        """Đơn `reserved` thiếu `reserved` trong scenario: cấp theo order_tick rồi id bàn, lấy tươi nhất rồi id nhỏ."""
        for c in sorted(pending, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
            got = self._try_reserve(self.menu[c["dish_id"]]["recipe"])
            if got is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = got

    # ---- hao tươi (đầu bước, sau timer) ------------------------------------------------------------
    def _decay_stock(self, events):
        """Hao kho thô (kể cả hàng đang giữ), phát hết `spoiled` theo id rồi mới xử lý giữ chỗ bị ươn."""
        if not self.item_mode:
            return
        newly = []
        for it in self.stock:
            before = it["units"]
            it["units"] = max(0, before - self._decay_units)
            if before >= self._spoil_units > it["units"]:
                newly.append(it)
        for it in sort_by_id(newly):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        if newly:
            self._rereserve_after_spoil({it["id"] for it in newly})

    def _rereserve_after_spoil(self, spoiled_ids):
        """Đơn bị ảnh hưởng (theo order_tick rồi id bàn): nhả toàn bộ phần giữ, thử giữ lại ĐÚNG MỘT LẦN."""
        affected = [c for c in self.customers
                    if c["order_status"] == "reserved" and spoiled_ids.intersection(c["reserved"])]
        for c in sorted(affected, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
            c["reserved"] = []
            got = self._try_reserve(self.menu[c["dish_id"]]["recipe"])
            if got is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = got

    # ---- snapshot / bàn giao -----------------------------------------------------------------------
    def _stock_snapshot(self):
        if not self.item_mode:
            return {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return [{"id": it["id"], "kind": it["kind"], "fresh": from_units(it["units"])}
                for it in sort_by_id(self.stock)]

    def stock_items_out(self):
        """Kho dạng mảng `{id, kind, fresh}` sắp theo id (bàn giao cho Shop / ngày kế)."""
        return self._stock_snapshot() if self.item_mode else []

    # ---- móc nối M4: nấu ----------------------------------------------------------------------------
    def _consume_reserved(self, cust):
        """Lấy khỏi kho đúng các id đang giữ của đơn, xóa phần giữ. Trả cá thể `{id, kind, fresh, units}`
        sắp theo (kind, id) — M4 dùng để chốt `base_price` (trung bình fresh) và `cook_started.items`."""
        ids = set(cust["reserved"])
        taken = [it for it in self.stock if it["id"] in ids]
        self.stock = [it for it in self.stock if it["id"] not in ids]
        cust["reserved"] = []
        taken.sort(key=lambda it: (it["kind"], id_key(it["id"])))
        return [{"id": it["id"], "kind": it["kind"], "fresh": from_units(it["units"]), "units": it["units"]}
                for it in taken]
