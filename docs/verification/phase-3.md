# Ma trận truy vết Phase 3

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-3/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P3-30 (lát 3) kho quán cá thể | `tests/test_quan_v12_stock.py::StockSchema` (snapshot `stock` là mảng `{id,kind,fresh}` sắp theo id; hàng ươn vẫn trong kho; `ItemIds` nối sau id đã nạp) | [lat3-quan-stock-v12.txt](../proof/phase-3/lat3-quan-stock-v12.txt) | đạt với tuning v1.2 trong test; chờ bật manifest 1.2 (p25) |
| AC-P3-31 (lát 3) hao tươi + ươn | `Decay`, `Spoiled` (0.25/s kể cả hàng giữ, kẹp 0; fresh đúng 30 ươn ở bước đầu; phát `spoiled` location `stock` đúng một lần, nhiều cá thể theo id; hàng ươn không dùng để gọi món → `no_dish`) | như trên | đạt |
| AC-P3-32 (lát 3) giữ chỗ theo id | `ReserveById` (tươi nhất, hòa theo id; bỏ qua hàng ươn; khách sau lấy phần còn lại) | như trên | đạt |
| AC-P3-33 (lát 3) giữ lại khi phần giữ vừa ươn | `ReReserve` (nhả toàn bộ, giữ lại đúng một lần; thiếu → `unfulfillable`, khách chờ tới hết kiên nhẫn, bếp không nấu đơn đó; nhiều đơn theo order_tick rồi id bàn — clarify #17) | như trên | đạt |
| AC-P3-34 (lát 3) fixture v1.2 | `FixtureV12`, `ScenarioFileV12` (reserved mảng id; bỏ trống thì cấp theo order_tick rồi id bàn sau phần giữ tường minh; id không có / đã ươn / khác công thức / dùng chung / đơn không phải reserved mà giữ → mã 2; giá chốt ≤ niêm yết — clarify #18) | như trên | đạt |
| (lát 4 + lát 3) nấu tiêu đúng id, giá theo tươi | `CookWithIds` (`cook_started.items` mảng cá thể sắp kind rồi id, `base_price = floor(giá × TB fresh / 100)`, cá thể đã dùng rời kho) | như trên | đạt — len2412 rà lại phần `_cook_at` |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
