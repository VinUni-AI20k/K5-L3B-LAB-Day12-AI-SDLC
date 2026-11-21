# Ma trận truy vết Phase 2

Mỗi người thêm dòng cho phần mình.
Kết quả ghi theo commit đã chạy kiểm; "chờ merge" nghĩa là đạt trên nhánh, chưa có trên `main`.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt - ghi trung thực) |
|---|---|---|---|
| C-P2-1 Quán 2 bếp, 4 bàn, 6 món theo dữ liệu (DoD 1) | Nền v1.1 của A (#8) có dữ liệu; `test_lat3_khach.test_het_ban_trong_thi_bo_luot` lấp đủ T1-T4 thì bỏ lượt; `test_lat3_p2.test_quan_rieng_dung_ca_6_mon` gọi được món mới `ca_keo_nuong` | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt) | Đạt trên nhánh `p2/thedlcrimson/day-loop` @ b6b580a, chờ merge PR #10, #11 |
| C-P2-2 Khách chọn món trong kế hoạch Ngày rồi mới lọc kho khả dụng, không giới hạn số suất | `tests/test_lat3_p2.py` (5 test): lọc kế hoạch trước kho, món ngoài kế hoạch không cứu `no_dish`, khách thứ 4 vẫn gọi khi kế hoạch 3 suất, kế hoạch có món ngoài menu thì mã 2 | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt), [lat3-day-2-ngay.txt](../proof/phase-2/lat3-day-2-ngay.txt) (khách Ngày 1 chỉ gọi món của D1) | Đạt trên nhánh, chờ merge PR #10 |
| C-P2-3 Scenario `day` kiểm tiền, uy tín, nâng cấp, `day_plan`; cấm `quan.stock`, `quan.reputation` | `tests/test_lat3_day_scenario.py` (10 test), mâu thuẫn trả `BadInput` (mã 2) | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt) | Đạt trên nhánh, chờ merge PR #10 |
| C-P2-4 `--mode day` công bố đúng kế hoạch D1-D5, chốt Ngày khi Shop đóng (DoD 2) | `tests/test_lat3_day.py`: `day_start` → `day_plan` → `phase_start` ở tick 0, đổi pha cùng tick ở 10.800 / 21.600 / 22.200, Ngày 2 mở đúng tick Shop đóng với kế hoạch D2, `days_complete` | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt), [lat3-day-2-ngay.txt](../proof/phase-2/lat3-day-2-ngay.txt) | Đạt trên nhánh, chờ merge PR #11 |
| C-P2-5 Shop mua `oxygen`/`hp`, áp dụng từ Ngày kế (DoD 2) | `test_lat3_day.test_mua_nang_cap_hieu_luc_tu_ngay_ke` và 4 test `ShopSim`: đủ đúng giá vẫn mua, `funds`, `max_level`, `unknown`, buy trước `shop_done`, tự đóng sau 600 bước | [lat3-day-2-ngay.txt](../proof/phase-2/lat3-day-2-ngay.txt): mua oxygen cấp 1 ở Ngày 1, Ngày 2 có `active_upgrades {"oxygen": 1}`, `oxygen_max_ticks` 2700 | Đạt trên nhánh, chờ merge PR #11 |
| C-P2-6 Pause dừng đồng hồ Shop | `test_lat3_day.test_pause_dung_dong_ho_shop`: 99 bước pause không tăng `phase_tick`, `sim_tick` | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt) | Đạt trên nhánh, chờ merge PR #11 |
| C-P2-7 Một Ngày không pause chạy headless dưới 20 s | `test_lat3_day.test_mot_ngay_khong_input_dung_thu_tu_pha_va_tick` đo thời gian; chạy 2 Ngày thật | [lat3-day-2-ngay.txt](../proof/phase-2/lat3-day-2-ngay.txt): 2 Ngày trong 0,51 s trên máy dev | Đạt trên nhánh, chờ merge PR #11 |
| C-P2-8 Regression P1 với số chuẩn | Toàn bộ test trên nhánh: 149 test, 1 đỏ là `test_e_qa_p1` (của E, đòi `contract_version` 1.0), không do lát 3. Sửa 1 dòng `test_smoke_p1` vì v1.1 bật `--mode day` (lý do trong commit) | [lat3-tests.txt](../proof/phase-2/lat3-tests.txt) | Chưa đạt trên toàn nhánh: còn 1 test đỏ của E |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
