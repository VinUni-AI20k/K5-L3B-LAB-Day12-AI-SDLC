# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Gather: giỏ đầy | Unit test nhặt tại nút khi hold đạt `hold_capacity`; kiểm tra `hold_full`, giỏ không đổi, nút chưa bị lấy | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Chưa đạt — luật nhặt còn TODO; regression test thất bại |
| Gather: ngạt nước | Unit test xác nhận chưa mất máu ở tick 59 và mất 1 HP đúng tick 60 theo `choke_interval_ticks` | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Chưa đạt — luật oxy/ngạt còn TODO; regression test thất bại |
| Gather: cây hồi sinh | Nút khởi đầu chưa sẵn sàng với 2 tick; xác nhận `node_regrown` đúng tick và `ready` trở lại true | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Đạt — bộ đếm hồi sinh và event được kiểm chứng |
| Quán: hết kiên nhẫn | Khởi tạo khách còn 2 tick, xác nhận chưa rời ở tick đầu và phát `customer_left` khi về 0 | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Chưa đạt — vòng đời khách còn TODO; regression test thất bại |
| Quán: tip phục vụ nhanh | Hoàn tất phục vụ trong trạng thái còn đủ `tip_min_patience_ratio`; đối chiếu tip với `price × tip_rate` | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Chưa đạt — thanh toán/tip còn TODO; regression test thất bại |
| Tính tất định headless | Chạy cùng mode/seed/ticks hai lượt, so SHA-256 của JSONL | [smoke_test.txt](../proof/phase-1/smoke_test.txt) | Đạt — hai file trùng hash SHA-256 |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đạt hồi sinh cây và tính tất định headless; bốn luật còn lại chưa đạt vì luật mô phỏng chưa được triển khai.
- Điều cần chỉnh: dev hoàn tất bốn luật đang TODO; QA chạy lại unittest để xác nhận regression tests chuyển xanh.
