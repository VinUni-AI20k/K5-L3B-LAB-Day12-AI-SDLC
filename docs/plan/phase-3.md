# Kế hoạch Phase 3 · TV4

Theo [phân công Phase 3](../phan-cong.md) và [TICKET-03](../../PHASE-3.md).

| Phạm vi TV4 | File | Test bị ảnh hưởng |
|---|---|---|
| Tiêu nguyên liệu theo ID, chốt giá tại lúc nấu, giữ giá qua phục vụ và thu tiền | `chonoi/sim/quan.py` | Thêm test ID, thứ tự payload, boa và floor. Giữ hồi quy giá niêm yết v1.1 trong lúc chuyển. |
| Giữ ID và fresh qua chuyển pha, cấp ID mẫu ngày sau, chuyển tham chiếu đơn fixture, chụp kho Shop | `chonoi/sim/day.py` | Thêm fixture day hai ngày. Giữ test chuyển pha, pause, mua và đóng Shop của Phase 2. |

Ghép adapter của TV1, giỏ cá thể của TV2 và kho cá thể của TV3. Trong `QuanSim`, dùng `_start_cooking` và `_consume_reserved_units` của TV4 thay phần nấu tạm trên nhánh TV3. Sau khi thống nhất biểu diễn độ tươi và ghép hai đầu, chạy lại các ca biên giá, smoke file/day và regression trên bản v1.2. [Kết quả hiện tại](../proof/phase-3/tv4-bep-vong-ngay.md)
# Kế hoạch Phase 3 (TV3)

- Mục tiêu: AC-P3-03 — kho cá thể quán, hao tươi, spoiled, giữ chỗ theo id, thử giữ lại / unfulfillable.
- Việc: `chonoi/freshness.py` · dual-mode `QuanSim` · `tuning.freshness` · test/proof `tv3-fresh-stock`.
- Phụ thuộc: TV1 adapter file + bump 1.2; TV4 chốt boa/day trên giá đã chốt; TV2 gather hold cá thể.
- Rủi ro: đụng `quan.py` / `scenario.py` với TV4; JSONL làm tròn fresh 3 chữ số.
