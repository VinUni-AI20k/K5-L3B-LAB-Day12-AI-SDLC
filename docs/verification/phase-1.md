# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-30 | `tests/test_quan_customers.py::Schedule` (khách ở tick 120, +900, bàn id nhỏ nhất, hết bàn bỏ lượt, chạy qua headless) | [lat3-quan-customers.txt](../proof/phase-1/lat3-quan-customers.txt) | đạt (sự kiện theo hợp đồng mục 3) |
| AC-P1-31 | `DishChoice` (chỉ món đủ kho khả dụng, `no_dish {}`, luồng RNG `customers`, trừ phần đang giữ, cùng seed cùng món, 60 seed phủ đủ menu) | như trên | đạt |
| AC-P1-32 | `Reservation` (giữ đúng công thức, không trừ tồn, `_release` nhả giữ + bỏ món trên bếp/tay) | như trên | đạt |
| AC-P1-33 | `Patience` (rời ở tick 120+3600, `reason: patience`, uy tín −0.5, kẹp min, khách đang ăn không giảm) | như trên | đạt |
| AC-P1-34 | `Fixture` (fixture hợp lệ → snapshot đúng; 14 kiểu mâu thuẫn → mã 2 (gồm assigned không có món, unfulfillable có món, eating sai giá); giữ chỗ quá kho `--inventory` → mã 2) | như trên | đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
