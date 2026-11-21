# Bằng chứng Lát 4 – Phase 2 (snapshot `main (5)`)

**Người thực hiện:** `nguyenhung1901` (bếp, phục vụ, tiền, uy tín). **Nguồn yêu cầu:** `docs/prd/phase-2.md`, `docs/plan/phase-2.md`, `docs/contracts/README.md`.

**Lệnh thử:** `python -m unittest discover -s tests -p "test_quan_lat4.py" -v` (cần để Python tìm thấy `tests/helpers.py`, ví dụ trên PowerShell đặt `$env:PYTHONPATH = "tests;."`). Đầu ra thật: [`lat4-unittest.txt`](lat4-unittest.txt).

| AC | Kiểm thử | Kết quả trên snapshot |
|---|---|---|
| AC-P2-05 | `test_ac_p2_05_chon_bep_truoc_ban_va_id_khi_hoa`, `test_ac_p2_05_4_ban_khi_hoa_khoang_cach_chon_id`, `test_ac_p2_05_sau_mon_tu_cong_thuc_va_gia_trong_menu`, `test_oldest_order_then_table_id` | PASS – 2 bếp / 4 bàn / 6 món trong manifest v1.1 |
| AC-P2-06 | `test_ac_p2_06_tien_va_uy_tin_carry_shift_earned_reset` | PASS – giữ `money`, `earned`, `reputation`, đặt lại `shift_earned` |
| AC-P2-08 | `test_ac_p2_08_snapshot_hud_quan_du_du_lieu` | PASS – chỉ xác nhận dữ liệu; **giao diện chưa được xác nhận đạt 18 px hoặc cảnh báo <25%** |
| AC-P2-12 | `test_ac_p2_12_dung_1200_tick_bung_duoc_1201_moi_chay`, `test_ac_p2_12_hai_bep_chay_cung_tick_giu_lai_co_han` | PASS với `burn_s: 20` trong tuning test, **chưa bật trong manifest** |

**Hồi quy toàn repo trên snapshot `(5)`:** `PYTHONPATH=tests:. python -m unittest discover -s tests -v` → **172 test, OK, không SKIP** (môi trường kiểm tra Linux/Python 3.13.5). Bản Windows của nhóm cần chạy lại trước khi tag/merge.

## Việc phải phối hợp trước khi chốt Phase 2

- **Lát 0 / Integrator:** `game.contract.json` hiện `extensions: []` và `tuning.quan.burn_s: null`. Quyết định I-1 yêu cầu bật `burn`. Nhưng `chonoi/contract.py` (dòng điều kiện `if q.get("burn_s") is not None`) đang từ chối giá trị hữu hạn, nên **phải sửa validator đồng thời với manifest**; đừng chỉ đổi JSON.
- **Lát UI / Tiệp:** HUD hiện đọc được dữ liệu trạng thái nhưng chữ thông tin bếp/bàn nhỏ hơn 18 px, không có màu cảnh báo kiên nhẫn dưới 25%. Cần chỉnh `chonoi/web/index.html` và cung cấp ảnh chụp 1280×720. Lát 4 không sửa file UI do Tiệp sở hữu.
- **QA Lead:** bổ sung các test trên vào `docs/verification/phase-2.md` sau khi merge, chạy lại trên commit tích hợp/tag.
