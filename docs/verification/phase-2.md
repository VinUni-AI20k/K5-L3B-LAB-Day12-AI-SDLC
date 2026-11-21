# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P2-31 | `tests/test_quan_p2_tables_plan.py::FourTables`, `SixDishes` (preset v1.1 có T1–T4 và 6 món; khách vào T1→T4 theo id; 4 bàn đầy thì bỏ lượt; bàn id nhỏ nhất vừa trống được dùng lại; quán độc lập chọn đủ 6 món qua 80 seed; món mới chỉ khi đủ công thức) + chạy headless quán độc lập kho 6 nguyên liệu | [lat3-quan-tables-plan.txt](../proof/phase-2/lat3-quan-tables-plan.txt) | đạt |
| AC-P2-32 | `DayPlanFilter` (chỉ món trong kế hoạch dù món khác đủ nguyên liệu; chỉ có món ngoài kế hoạch → `no_dish`; lọc kế hoạch rồi mới lọc kho; kế hoạch 1 suất vẫn gọi tiếp 3 suất; cùng seed cùng món; món kế hoạch D1–D5 đều có trong menu; fixture ngoài kế hoạch → `BadInput` (clarify #16)) + `DayModeIntegration` qua `--mode day` (Ngày 1 chỉ gọi món kế hoạch dù kho đủ món khác; chỉ có món ngoài kế hoạch → `no_dish`; khách dựng sẵn ngoài kế hoạch → mã 2) | như trên | đạt (cả `QuanSim` và `--mode day`; đã sửa `day.py` dùng `menu_filter` thay vì cắt menu — trước đó fixture ngoài kế hoạch gây KeyError mã 1) |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
