# Changelog
## Unreleased — Test Contract v1.2 (Phase 3, CR "Mùa Nước Nổi")

### Breaking change
- **File kho đếm → kho cá thể.** v1.1 `{"items":{"ca_loc":1}}` → v1.2 `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`, sắp theo id, kho rỗng `{"items":[]}`. Contract v1.2 trả **mã 2** cho file kho đếm, kind lạ, id trùng, `fresh` ngoài [0, 100].
- `gather.hold`, `quan.stock` trong scenario là **mảng cá thể**; `customers[].reserved` là **mảng id**. `gather_end.data.inventory`, snapshot `hold` / `stock`, `cook_started.data.items`, `lost` của `monster_hit` / `faint` đều là mảng cá thể.
- `base_price` chốt theo độ tươi lúc bắt đầu nấu: `floor(giá niêm yết × trung bình fresh / 100)`.
- Manifest: `contract_version: "1.2"`, thêm `tuning.freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

### Cập nhật fixture
- `hold: ["ca_loc"]` → `hold: [{"id": "I1", "kind": "ca_loc", "fresh": 100}]` (id `I1, I2, …` theo thứ tự vào giỏ).
- `stock: {"ca_loc": 1}` → `stock: [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`; `reserved: {"ca_loc": 1}` → `reserved: ["I1"]`.
- Id vật lý duy nhất giữa giỏ, kho, phần giữ.

### Thêm
- `chonoi/items.py`: cá thể + độ tươi bằng đơn vị nguyên (240 đơn vị / điểm), `ItemIds`, `decay()`, `pick_freshest()`, `price_by_fresh()`.
- `chonoi/inventory.py` đọc / ghi cả hai schema (chọn theo manifest có `freshness`).
- `tests/test_inventory_v12.py`.

## v1.1 — Phase 2 (tag `phase-2`)
- Số chuẩn TICKET-02, 6 nguyên liệu / 6 món, cá bơi / sinh, Cá Sấu, 2 bếp / 4 bàn, `--mode day`, Shop, pause.

## v1.0 — Phase 1 (tag `phase-1`)
- Lõi gather / quán, file kho đếm, headless tất định.
