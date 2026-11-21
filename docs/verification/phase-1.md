# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Gather: giỏ đầy | Unit test nhặt tại nút khi hold đạt `hold_capacity`; kiểm tra `hold_full`, giỏ không đổi, nút chưa bị lấy | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — đã kiểm chứng qua `test_interact_with_full_hold_emits_hold_full_without_changing_hold` và `test_11_hold_full_plant` |
| Gather: ngạt nước | Unit test xác nhận chưa mất máu ở tick 59 và mất 1 HP đúng tick 60 theo `choke_interval_ticks` | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — đã kiểm chứng qua `test_choke_damages_only_after_full_60_tick_interval` và `test_05_choke_reduces_hp` |
| Gather: cây hồi sinh | Nút khởi đầu chưa sẵn sàng với 2 tick; xác nhận `node_regrown` đúng tick và `ready` trở lại true | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — bộ đếm hồi sinh và event được kiểm chứng qua `test_08_plant_regrowth` |
| Quán: hết kiên nhẫn | Khởi tạo khách còn 2 tick, xác nhận chưa rời ở tick đầu và phát `customer_left` khi về 0 | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — đã kiểm chứng qua `test_customer_leaves_on_tick_patience_reaches_zero` và `test_customer_patience_and_left` |
| Quán: tip phục vụ nhanh | Hoàn tất phục vụ trong trạng thái còn đủ `tip_min_patience_ratio`; đối chiếu tip với `price × tip_rate` | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — đã kiểm chứng qua `test_fast_service_tip_uses_contract_rate_and_menu_price` và `test_full_cooking_serving_and_payment_flow` |
| Tính tất định headless | Chạy cùng mode/seed/ticks hai lượt, so SHA-256 của JSONL | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | **Đạt** — hai file trùng hash SHA-256 tuyệt đối qua skill `verify-phase` |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:** ĐÃ ĐẠT 100% tất cả các tiêu chí chấp nhận (AC) của Phase 1. Toàn bộ 57/57 unit tests, smoke tests và edge tests đều xanh.
- **Điều cần chỉnh cho phase sau:** Tiếp tục duy trì quy trình kiểm thử tự động hộp đen và mở rộng logic mô phỏng cho chu kỳ ngày đêm liên tục (`day`) trong Phase 2.
