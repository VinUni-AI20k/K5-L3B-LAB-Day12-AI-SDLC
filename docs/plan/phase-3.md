# Kế hoạch Phase 3 — TICKET-03 "Mùa Nước Nổi" (Test Contract v1.2, chỉ phần Lõi "Độ tươi")

## Tác động (Module | File | Test | Người phụ trách — theo TEAM.md)
| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter (schema kho, contract) | `game.contract.json` (1.2 + freshness), `chonoi/contract.py`, `chonoi/inventory.py` | thêm `tests/test_inventory_p3.py`; `test_smoke_p1` (file kho) đổi | Cao Duy Minh |
| Lặn | `chonoi/sim/gather.py` (giỏ cá thể, hao 0.5/s, spoiled hold) | `test_gather_p1/p2` đi qua lớp chuyển fixture | Cao Duy Minh |
| Quán | `chonoi/sim/quan.py`, `chonoi/scenario.py` (quan.stock, reserved theo id) | thêm `tests/test_quan_p3.py`; `test_quan_p1/p2` qua `tests/v12_compat.py`, giá 60→59, 200→199 | Duyet |
| day / Shop | `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/runner.py`, `chonoi/headless.py` | `test_day_p2` qua lớp chuyển; thêm `tests/test_smoke_p3.py` | Nhat Minh |
| HUD / QA | `client/` (độ tươi, nhãn ươn), `docs/proof/phase-3/`, `docs/verification/phase-3.md` | smoke bàn giao + regression P1–P2 | Nhat Minh |

## Quyết định đổi schema
- Kho đếm `{"items":{kind:n}}` → kho cá thể `{"items":[{id,kind,fresh}]}`; chọn theo `contract_version` (1.2 → file đếm mã 2).
- Bên trong lưu độ tươi bằng đơn vị nguyên `units` (240/điểm): gather −2/tick, quán −1/tick → ngưỡng 30 và floor giá chính xác.
- Snapshot `hold`/`stock`/`customers[].reserved` dùng schema mới; event `spoiled {item_id,kind,location}`.

## Thứ tự tích hợp (giữ main chạy)
1. Adapter: `inventory.py` có helper v1.2 + đọc được cả 2 schema theo version (chưa bật 1.2).
2. Lớp chuyển fixture `tests/v12_compat.py` để regression P1–P2 vẫn chạy khi đổi schema.
3. Lặn và Quán song song trên helper đã chốt; day/Shop nối bàn giao trong bộ nhớ.
4. Bật `contract_version: "1.2"`, chạy smoke bàn giao file (`docs/proof/phase-3/run_proof.sh`) + `day --days 2` + full test.
