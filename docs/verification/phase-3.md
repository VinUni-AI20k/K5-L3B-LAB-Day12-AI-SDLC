# Ma trận truy vết Phase 3 — Test Contract v1.2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Ngưỡng ươn trong giỏ | Cá thể ở fresh 30 lúc dựng fixture. Chạy hai tick, kiểm spoiled chỉ phát ở tick 1 và hàng vẫn chiếm ô | [Test QA Phase 3](../../tests/test_qa_phase3.py) | **ĐẠT (PASS)**: `test_gather_item_at_threshold_spoils_once_on_first_tick` chạy qua headless thành công. |
| Bàn giao kho cá thể qua file | So id, kind và fresh giữa gather_end, file xuất và snapshot quán tick 0 | [Test QA Phase 3](../../tests/test_qa_phase3.py) | **ĐẠT (PASS)**: `test_quan_imports_gather_item_with_same_id_and_freshness` khớp id, kind và độ tươi sau hao 1 tick. |
| Từ chối kho đếm | Nạp `{"items":{"ca_loc":1}}` vào quán. Với v1.2, kiểm mã thoát 2 và không tạo JSONL | [Test QA Phase 3](../../tests/test_qa_phase3.py) | **ĐẠT (PASS)**: `test_quan_rejects_count_inventory_without_writing_output` trả mã 2 và không ghi file ra. |
| Giữ lại nguyên liệu và chốt giá | Kiểm đơn có hàng vừa ươn, chọn lại cá thể và tính giá theo fresh lúc nấu | [Bằng chứng Quán](../proof/phase-3/quan-sim.md) · [Test Quán](../../tests/test_quan.py) | **ĐẠT (PASS)**: 10/10 test Quán Phase 3 pass, chốt base_price = floor(listed * avg_fresh / 100). |

## Tác động lên regression P1–P2

- Khi bật v1.2, đổi fixture giỏ từ mảng mã nguyên liệu sang mảng cá thể. Cập nhật assertions cho lost, stock và file kho theo schema mới.
- Giữ kiểm tra LIFO, ngất, kho rỗng và không ghi đè file khi dừng do giới hạn tick.
- Ghi nhận breaking change trong `CHANGELOG.md` và bằng chứng tích hợp tại `docs/proof/phase-3/quan-sim.md`.
