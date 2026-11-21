# QA Phase 2 · báo cáo tự động (`python3 tools/qa_p2.py`)

- Commit: `a90aab5 (+ thay đổi chưa commit)`
- Máy đo: macOS-26.5.2-arm64-arm-64bit-Mach-O · Python 3.13.9 · arm64
- Thời điểm chạy: 2026-11-21 11:25:15

| CP | Kiểm tra | Kết quả | Chi tiết |
|---|---|---|---|
| CP1 | Smoke gather `--inventory-out` → quan `--inventory` (6 loại) | **PASS** | gather_end={'bong_dien_dien': 1, 'bong_sung': 2, 'ca_keo': 2, 'ca_linh': 1, 'ca_loc': 1, 'keo_neo': 1} · file={'bong_dien_dien': 1, 'bong_sung': 2, 'ca_keo': 2, 'ca_linh': 1, 'ca_loc': 1, 'keo_neo': 1} · stock@0={'bong_dien_dien': 1, 'bong_sung': 2, 'ca_keo': 2, 'ca_linh': 1, 'ca_loc': 1, 'keo_neo': 1} |
| CP2 | Headless day --days 1 trọn Ngày, không pause (≤ 22.200 tick, ≤ 20 s) | **PASS** | 0.23 s · 22200 tick · reason=days_complete · days_completed=1 · mở đầu ['day_start', 'day_plan', 'phase_start'] |
| CP3 | day --days 2: money=earned=200, mua oxygen + shop_done cùng frame | **PASS** | bought={'upgrade': 'oxygen', 'level': 1, 'price': 200, 'money': 0} · shop_end=[{'reason': 'done'}, {'reason': 'done'}] · D2 oxy_max=2700 active={'oxygen': 1} · end money=0 earned=200 days_completed=2 |
| CP4 | Pause headless (đứng sim_tick + đồng hồ, chỉ tăng tick ngoài) | **PASS** | event=[(11, 'paused'), (111, 'resumed')] · sim_tick@11=10 @110=10 @111=11 · time_left@11=10790 @110=10790 |
| CP5 | Ngất → gather_end(fainted) → phase_start(quan) cùng tick, kho rỗng | **PASS** | [(60, 'gather', 'faint'), (60, 'gather', 'gather_end'), (60, 'quan', 'phase_start')] · stock quán@0={} |
| CP6 | Tất định day seed 7 (3.000 tick × 2 lần) | **PASS** | sha256 ed086137f861a572 / ed086137f861a572 |
| CP7 | Regression toàn suite (P1 còn hiệu lực + P2) | **PASS** | Ran 95 tests in 6.901s · OK (7.0 s) |
