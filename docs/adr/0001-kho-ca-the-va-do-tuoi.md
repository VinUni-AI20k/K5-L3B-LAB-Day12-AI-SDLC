# ADR-0001: Kho cá thể + độ tươi (contract v1.2)

- Trạng thái: **chấp nhận** (change request Phase 3)
- Ngày, người quyết: Phase 3 kickoff — Integrator + QA, cả nhóm chốt
- Thay thế: schema kho đếm của v1.0/v1.1

## Bối cảnh

PRD Phase 3 đổi kho từ `{"items": {"ca_linh": 3}}` sang `{"items": [{"id":"I1","kind":"ca_linh","fresh":100}]}`.
Đây là thay đổi **lan ra mọi nơi**: file kho, scenario, snapshot, event, fixture test, HUD, và cả bàn giao
trong `day`. Làm big-bang sẽ làm đỏ toàn bộ test trong lúc chuyển, không ai biết mình làm hỏng cái gì.

Ràng buộc kèm theo từ PRD: độ chính xác ở **ngưỡng ươn 30**, phép `floor` khi chốt giá, `spoiled` phát đúng
một lần, LIFO khi mất hàng, và id cá thể tăng xuyên pha/Ngày.

## Các lựa chọn đã cân nhắc

1. **Big-bang**: đổi schema một lần, sửa hết test trong cùng commit. Nhanh trên giấy, nhưng main đỏ suốt
   quá trình, và không thể chạy regression P1–P2 trong lúc chuyển.
2. **Adapter hai schema** trong lớp kho, chọn theo `contract_version`; sim chỉ nói chuyện với một API duy nhất.
   Main luôn xanh; bật v1.2 khi cả gather và quán đã bàn giao.
3. **Module song song** (`inventory_v12.py`) rồi xóa bản cũ. Sạch hơn về lâu dài nhưng nhân đôi code kho trong
   lúc chuyển, và dễ sót chỗ còn gọi bản cũ.

## Quyết định

Chọn **2 — adapter hai schema**. Cụ thể:

- Một lớp `Stock` (trong `chonoi/inventory.py`) là API duy nhất cho sim: `add(kind, units)`, `take(...)`,
  `items()`, `fresh_of(id)`… Sim không biết schema trên đĩa.
- Đọc/ghi file chọn schema theo `contract_version`; v1.2 **từ chối** file đếm bằng mã 2 và ngược lại.
- **Độ tươi lưu bằng số nguyên đơn vị**: 1 điểm = 240 đơn vị. Hao 2 đơn vị/tick (giỏ), 1 đơn vị/tick (quán),
  ngưỡng ươn 7 200 đơn vị. Chỉ đổi sang điểm khi xuất JSONL.
- Id cá thể cấp bằng `IdAllocator` tiền tố `I`, tăng xuyên pha và xuyên Ngày.

**Điều kiện bật v1.2:** gather và quán đều đã dùng `Stock`; test migration xanh; smoke hai tiến trình xanh
trên schema mới.

## Hệ quả

- Main xanh trong suốt quá trình chuyển; regression P1–P2 chạy được ở cả hai schema.
- Thêm một lớp gián tiếp; ai đọc code phải hiểu "units" trước khi đọc `fresh`.
- Test cũ dùng schema đếm vẫn chạy khi `contract_version` < 1.2 — không phải sửa hàng loạt fixture cùng lúc.

## Bảng tác động

| Module | File | Test bị ảnh hưởng | Người |
|---|---|---|---|
| Kho + adapter | `chonoi/inventory.py` | `test_smoke_p1.py` (integration), `test_python_starter_units.py` | Cao Minh |
| Contract | `chonoi/contract.py` (thêm `freshness`, version 1.2) | `test_python_starter_units.py` | Cao Minh |
| Lặn | `chonoi/sim/gather.py`, `chonoi/sim/gather_actions.py` | `test_gather_rules.py`, `test_gather_actions.py` | Nhật Minh |
| Quán | `chonoi/sim/quan.py`, `quan_customers.py`, `quan_service.py` | `test_quan_rules.py`, `test_quan_service.py` | Đức Minh |
| Bàn giao / day | `chonoi/runner.py`, `chonoi/sim/day.py` (P2) | `test_day*.py` (P2) | Cao Minh |
| HUD | `chonoi/web/index.html` | — (kiểm bằng mắt + ảnh) | Vinh |
| QA | `tests/test_migration_v12.py` (mới), `docs/verification/phase-3.md` | tất cả | Văn Minh |
| Ghi chép | `CHANGELOG.md`, `docs/clarify.md` | — | Đức Minh |

## Cách cập nhật fixture (ghi vào CHANGELOG)

- v1.1 → v1.2: `{"ca_loc": 1}` thành `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]`; id phải duy nhất
  trong toàn bộ scenario; `customers[].reserved` từ map `kind → số` thành **mảng id**.
- Muốn kiểm nhánh ươn: đặt `fresh: 30` — sang bước đầu tiên là ươn và phát `spoiled`.
