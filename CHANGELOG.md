## [Phase 3] Contract v1.2 — Độ tươi (TICKET-03)
### Breaking
- `contract_version` 1.2, thêm `tuning.freshness {initial,gather_decay_per_s,quan_decay_per_s,spoiled_below}` = 100, 0.5, 0.25, 30.
- File kho: `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}` (sắp theo id). Quán v1.2 trả mã 2 cho file kho đếm.
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id cá thể.
- Snapshot `hold`/`stock` (quán, Shop)/`customers[].reserved` theo schema mới; `cook_started.data.items` là mảng cá thể (kind rồi id).
- `base_price` chốt lúc bắt đầu nấu = floor(giá niêm yết × mean fresh / 100); boa tính trên giá chốt.
### Thêm
- Event `spoiled {item_id,kind,location}`; hao tươi kho quán 1 đơn vị/tick (240 đơn vị/điểm), pause dừng hao, Shop không hao.
### Cập nhật fixture
- Kho đếm `{"ca_loc":2}` → `[{"id":"S1","kind":"ca_loc","fresh":100},{"id":"S2",...}]`; `reserved {"ca_loc":1}` → `["S1"]`.
- Regression P1–P2 đi qua `tests/v12_compat.py` (lý do trong docstring); giá kỳ vọng 60→59, 200→199 vì luật giá theo fresh.

# Changelog
## Unreleased
