# Ma trận truy vết Phase 3 — Test Contract v1.2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Ngưỡng ươn trong giỏ | Cá thể ở fresh 30 lúc dựng fixture. Chạy hai tick, kiểm spoiled chỉ phát ở tick 1 và hàng vẫn chiếm ô | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline `8739a9f` trả mã 2 khi đọc `gather.hold` dạng cá thể. Chưa chạy tới bước hao tươi. |
| Bàn giao kho cá thể qua file | So id, kind và fresh giữa gather_end, file xuất và snapshot quán tick 0 | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline `8739a9f` trả mã 2 khi đọc `gather.hold` dạng cá thể. Luồng dừng trước khi xuất kho. |
| Từ chối kho đếm | Nạp `{"items":{"ca_loc":1}}` vào quán. Với v1.2, kiểm mã thoát 2 và không tạo JSONL | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline v1.1 tại `8739a9f` nhận kho đếm và thoát mã 0. Chờ kiểm lại khi bật v1.2. |
| Giữ lại nguyên liệu và chốt giá | Kiểm đơn có hàng vừa ươn, chọn lại cá thể và tính giá theo fresh lúc nấu | — | Chờ kiểm trên v1.2. |

## Tác động lên regression P1–P2

- Khi bật v1.2, đổi fixture giỏ từ mảng mã nguyên liệu sang mảng cá thể. Cập nhật assertions cho lost, stock và file kho theo schema mới.
- Giữ kiểm tra LIFO, ngất, kho rỗng và không ghi đè file khi dừng do giới hạn tick.
- Kiểm lại riêng hai lỗi Phase 2 còn mở là CLI thiếu `--days` và parser chưa nhận `pause`.