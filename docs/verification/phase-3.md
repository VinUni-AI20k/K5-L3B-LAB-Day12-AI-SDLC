# Ma trận truy vết Phase 3 — Contract v1.2

QA chạy trên `feat/qa-phase3`, được tạo từ `main` tại `9edd212`.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả trên main hiện tại |
|---|---|---|---|
| Schema kho cá thể v1.2 hợp lệ; kho đếm cũ trả mã 2 | `test_v12_inventory_accepts_individuals_and_rejects_legacy_counts`, `test_inventory_file_accepts_individual_item_schema`, `test_inventory_file_rejects_legacy_count_schema_with_exit_two` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: contract vẫn là 1.1; kho cá thể bị validator từ chối. |
| Hao tươi gather 0.5/s, quán 0.25/s; pause đóng băng | `test_freshness_decay_rates_and_pause_freezes_stock`, `test_inventory_freshness_manifest_values` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: chưa có tuning freshness; scenario kho cá thể chưa được nhận. |
| Mốc ươn 30 phát `spoiled` đúng một lần ở tick biên | `test_item_at_spoil_threshold_emits_one_event_on_boundary_tick` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: gather chưa nhận cá thể có id/độ tươi. |
| Giữ lại nguyên liệu tươi nhất theo ID sau khi phần giữ bị ươn | `test_spoiled_reserved_item_retries_with_freshest_valid_id` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: trường scenario `reservations` chưa được hỗ trợ. |
| Chốt giá theo độ tươi trung bình rồi tính tip | `test_price_uses_average_freshness_and_tip_is_calculated_after_price` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: schema kho cá thể chưa được nhận; chưa kiểm chứng công thức. |
| Bàn giao gather→quán nguyên tử qua file và trong mode day | `test_gather_file_handoff_is_atomic_and_day_handoff_preserves_freshness` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: schema cá thể bị từ chối trước khi chạy handoff. |
| Dòng lũ cảnh báo trước 120 tick, đẩy 1.5 m/s từ sâu 10 trong 480 tick | `test_current_manifest_contract_values`, `test_current_warns_at_lead_boundary_and_pushes_at_depth_ten` | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Chưa đạt: contract chưa khai báo `gather.current`. |
| Regression Phase 1–2 và tính tất định | `python -m unittest discover -s tests -v`; skill `verify-phase` (2 lần headless cùng seed) | [smoke_test.txt](../proof/phase-3/smoke_test.txt) | Regression có các test QA Phase 3 chưa đạt; headless lặp lại cho kết quả SHA-256 giống nhau. |

## Đánh giá

Đây là bộ acceptance tests và bằng chứng cho trạng thái `main` vừa kéo về, không phải xác nhận Phase 3 đã hoàn tất. Gameplay/schema Phase 3 chưa được tích hợp trong commit nền `9edd212`; cả 11 test Phase 3 đang thất bại (9 failures, 2 errors), còn 93 test regression hiện có đạt. Headless gather chạy lặp cho cùng SHA-256. Không sửa luật mô phỏng trong lát QA này. Cần tích hợp Contract 1.2 trước khi dùng kết quả để đóng phase.
