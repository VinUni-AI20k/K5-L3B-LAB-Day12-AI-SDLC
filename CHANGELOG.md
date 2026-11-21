# Changelog
## Unreleased

### Đã có trên nhánh QA (chưa phụ thuộc v1.2)
- Test hộp đen Phase 3 `tests/test_fresh_p3.py` (28 test, `@pending`, bật bằng `QA_STRICT=1`) và ma trận `docs/verification/phase-3.md`.
- HUD (`chonoi/web/index.html`) đọc được cả kho đếm (v1.1) lẫn kho cá thể (v1.2): thanh độ tươi, gạch chéo và cảnh báo hàng ươn, kho khả dụng bỏ phần giữ chỗ và hàng ươn.

### Dự kiến v1.2 — Ticket-03 "Mùa Nước Nổi" (chưa có hiệu lực trên `main`; cập nhật khi bật)
**BREAKING — kho đếm theo loại → kho cá thể.** `contract_version` đổi `"1.1"` → `"1.2"`, thêm `tuning.freshness`
`{initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

| Chỗ | Trước (v1.1) | Sau (v1.2) |
|---|---|---|
| File kho `--inventory` / `--inventory-out` | `{"items": {"ca_loc": 1}}` | `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`; kho rỗng `{"items": []}`; file kho đếm cũ → mã 2 |
| `gather.hold`, `quan.stock` (scenario) | mảng kind / map kind → số | mảng cá thể `{id, kind, fresh}` |
| `customers[].reserved` | map kind → số | mảng id cá thể |
| Giỏ, kho quán trong snapshot | mảng kind / map | mảng cá thể |
| `cook_started.data.items`, `lost` (monster_hit, faint), `gather_end.data.inventory` | mảng kind / map | mảng cá thể |
| Giá món | giá niêm yết | `floor(giá niêm yết × TB fresh các cá thể dùng / 100)`, boa tính trên giá đã chốt |
| Giữ chỗ | theo lượng | theo id: cá thể tươi nhất, hòa id nhỏ; vừa ươn thì nhả hết và thử giữ lại một lần |
| Sự kiện mới | — | `spoiled {item_id, kind, location}` |

**Cách cập nhật fixture:** đổi `"hold": ["ca_loc"]` thành `"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`; `"stock": {"ca_loc": 1}`
thành mảng cá thể; `"reserved": {"ca_loc": 1}` thành `"reserved": ["I1"]`; file kho cũ phải sinh lại bằng gather v1.2.
Test cũ bị thay bởi luật mới sẽ liệt kê (kèm lý do) ở `docs/verification/phase-3.md` mục AC-P3-19.
