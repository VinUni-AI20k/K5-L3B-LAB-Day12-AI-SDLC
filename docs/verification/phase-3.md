# Ma trận truy vết Phase 3 (Lát 2: Ngô Duy Khánh)

| AC | Nội dung yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | Kho cá thể v1.2: mảng cá thể `{id, kind, fresh}` | `test_phase3_slice2.py::test_handover_v12_inventory_file` | File kho và snapshot quán khớp schema cá thể | ĐẠT |
| AC-P3-02 | Hàng mới fresh = 100, cấp ID I1, I2... tăng liên tục | `test_phase3_slice2.py::test_harvest_creates_individual_item_fresh_100`, `test_catch_ca_linh_yield_creates_3_individual_items` | Hái/bắt sinh cá thể fresh=100.0, ID I1, I2, I3 | ĐẠT |
| AC-P3-03 | Hao tươi trong giỏ 0.5/s (60 tick giảm 0.5) | `test_phase3_slice2.py::test_freshness_decay_in_hold` | Sau 60 tick fresh từ 100.0 giảm còn 99.5 | ĐẠT |
| AC-P3-04 | Hàng ươn fresh < 30 phát event `spoiled` đúng 1 lần | `test_phase3_slice2.py::test_spoiled_event_at_threshold_30` | Tick 1 phát event `spoiled` `{item_id: "I1", kind: "ca_linh", location: "hold"}` | ĐẠT |
| AC-P3-05 | Bàn giao kho cá thể giữa 2 tiến trình gather và quan | `test_phase3_slice2.py::test_handover_v12_inventory_file` | `gather --inventory-out` ghi file, `quan --inventory` đọc đúng độ tươi | ĐẠT |
| AC-P3-06 | Từ chối file kho đếm kiểu cũ ở Contract v1.2 (mã thoát 2) | `test_phase3_slice2.py::test_reject_count_inventory_in_v12` | Chạy `quan --inventory` với kho đếm thoát mã 2 | ĐẠT |
| AC-P3-07 | Ngất mất hàng theo LIFO và xuất kho rỗng `{"items": []}` | `test_phase3_slice2.py::test_faint_lifo_lost_and_empty_inventory` | Event `faint` có `lost` dạng LIFO, file kho là `{"items": []}` | ĐẠT |

## Đánh giá ngắn
- **Đạt**: Hoàn thành toàn bộ chuyển đổi schema kho cá thể, cơ chế độ tươi, hao tươi trong giỏ, sự kiện `spoiled` và tương thích 2 chiều giữa Lặn & Quán.
- **Lưu ý**: Contract v1.2 là breaking change so với v1.0, các test mới được lưu trữ tập trung tại `tests/test_phase3_slice2.py`.
