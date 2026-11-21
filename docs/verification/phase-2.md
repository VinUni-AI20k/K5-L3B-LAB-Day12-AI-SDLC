# Ma trận kiểm chứng Phase 2 · Test Contract v1.1

> Chủ file: **TV5 (QA/Release)**. Mỗi dòng nối một yêu cầu của [TICKET-02](../../PHASE-2.md) với cách kiểm, bằng chứng và kết quả.
> Checkpoint của TV5 chạy lại bằng **một lệnh** `python3 tools/qa_p2.py` → [qa-report.md](../proof/phase-2/qa-report.md) (ghi commit, máy đo, thời điểm).
> Kết quả dưới đây chạy trên cây làm việc gồm main sau PR #11 (TV1–TV4 đã tích hợp) cộng phần TV5; chạy lại trên commit gắn tag `phase-2` trước khi đẩy tag.

## 1. Lõi · số liệu chuẩn và luật (các lát TV1–TV4)

| Yêu cầu | Chủ | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `contract_version:"1.1"`, tuning chuẩn, 6 nguyên liệu, 6 món theo dữ liệu | TV4 + TV3 | Đọc `game.contract.json`; CP1 chạy kho đủ 6 loại qua hai tiến trình | `game.contract.json` · [qa-report CP1](../proof/phase-2/qa-report.md) | **Đạt** |
| Cá bơi / phản xạ / đổi hướng ở bước 120·k, sinh ở 360·k, trần 12, 8 điểm ban đầu khác nhau, `random_fish:false` | TV2 | `tests/test_gather_fish_p2.py` | [tv2-fish.txt](../proof/phase-2/tv2-fish.txt) | **Đạt** |
| Cá Sấu patrol/chase/recoil, ngưỡng độ sâu và biên | TV1 | Fixture headless, so snapshot theo tick | [tv1-monsters.md](../proof/phase-2/tv1-monsters.md) | **Đạt** |
| Chạm: 1 hit/bước, bất tử 90, rơi `floor(n/2)` LIFO, ngạt xuyên bất tử, ngất do quái | TV1 | `tests/test_gather_monsters.py` | [tv1-monsters.md](../proof/phase-2/tv1-monsters.md) | **Đạt** |
| M2 từ Ngày 3 | TV1 | Dựng GatherSim với day = 1, 2, 3 | [tv1-monsters.md](../proof/phase-2/tv1-monsters.md) | **Đạt** |
| 2 bếp / 4 bàn, 6 món, day_plan D1–D5, ingredients = công thức × suất, lọc món theo kế hoạch | TV3 | `tests/test_quan_plan_p2.py` | [tv3-menu-plan.md](../proof/phase-2/tv3-menu-plan.md) · [18-hud-quan-2bep-4ban.jpg](../proof/phase-2/ui/18-hud-quan-2bep-4ban.jpg) | **Đạt** |
| `--mode day`, chuyển pha cùng tick, Shop, buy/buy_failed, cấp áp từ Ngày kế, `days_completed` | TV4 | `tests/test_day_cycle.py` | [tv4-vong-ngay.md](../proof/phase-2/tv4-vong-ngay.md) | **Đạt** |

## 2. Checkpoint tích hợp · TV5 chạy lại bằng CLI như máy chấm

| CP | Yêu cầu (TICKET-02 mục 5 / phân công) | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|---|
| CP1 | Smoke phút 20: gather `--inventory-out` → quan `--inventory`, đối chiếu kho ở tick 0 | Giỏ đủ 6 loại, cập bến tick 0; so `gather_end.inventory.items` = file kho = `stock` snapshot quán tick 0 | [integration.gather.jsonl](../proof/phase-2/integration.gather.jsonl) · [integration.inventory.json](../proof/phase-2/integration.inventory.json) · [integration.quan.jsonl](../proof/phase-2/integration.quan.jsonl) | **Đạt** — cả 3 bằng `{bong_dien_dien:1, bong_sung:2, ca_keo:2, ca_linh:1, ca_loc:1, keo_neo:1}` |
| CP2 | `day --days 1` trọn Ngày không pause ≤ 22.200 tick, ≤ 20 s; công bố đúng kế hoạch D1 | Seed 42, 22.200 tick; kiểm mở đầu `day_start → day_plan → phase_start`, plan D1, `days_complete` | [day1.jsonl](../proof/phase-2/day1.jsonl) | **Đạt** — 0.37 s, 22.200 tick, `days_completed:1` |
| CP3 | Fixture money=earned=200, mua oxygen và đóng Shop cùng frame; money 0, earned 200, oxy D2 = 2700, `days_completed` đúng | `day --days 2` + [day2.scenario.json](../proof/phase-2/day2.scenario.json) + [day2.inputs.json](../proof/phase-2/day2.inputs.json) | [day2.jsonl](../proof/phase-2/day2.jsonl) | **Đạt** — `bought` trước `shop_end(done)`, D2 `active_upgrades:{oxygen:1}`, `oxygen_max_ticks:2700`, end money 0 / earned 200 / `days_completed:2` |
| CP4 | Pause đứng timer, chỉ tăng tick ngoài, `paused`/`resumed`, resume chạy ngay | Cạnh pause ở tick 10 và 110, snapshot mỗi tick | [pause.jsonl](../proof/phase-2/pause.jsonl) | **Đạt** — `sim_tick` 10 → 10 suốt pause, `time_left` đứng 10.790, tick 111 `sim_tick` 11 |
| CP5 | Ngất vẫn mở quán với kho bàn giao rỗng | HP 1, oxy 0 dưới nước, giỏ có hàng | [faint.jsonl](../proof/phase-2/faint.jsonl) | **Đạt** — tick 60: `faint → gather_end(fainted) → phase_start(quan)`, stock quán `{}` |
| CP6 | Chạy lại cùng seed/input giống từng byte | day seed 7, 3.000 tick × 2 | [det_day_run1.jsonl](../proof/phase-2/det_day_run1.jsonl) · [det_day_run2.jsonl](../proof/phase-2/det_day_run2.jsonl) | **Đạt** — sha256 trùng |
| CP7 | Regression P1 còn hiệu lực với số chuẩn + test P2 | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | [test_suite.log](../proof/phase-2/test_suite.log) | **Đạt** — 95/95 |

Test P1 đổi theo v1.1 (chủ lát ghi lý do trong commit/PR): `tests/test_smoke_p1.py`, `tests/test_quan_customers.py`, `tests/test_gather_harvest.py` — cập nhật theo số chuẩn mới (N5/N6, 4 bàn, 6 món), không nới điều kiện kiểm.

## 3. Giao diện, pause, HUD, hiệu năng · TV5

Cửa sổ chơi `python3 -m chonoi.live --mode day` chạy **cùng DaySim với headless** (`runner.Session("day")`); [chonoi/live_day.py](../../chonoi/live_day.py) chỉ thêm màn chờ UI và gộp số liệu. Test: [tests/test_live_day.py](../../tests/test_live_day.py).

| Yêu cầu | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| Menu chính có Chơi, Thoát (+ Cài đặt) | Menu chưa bước sim, `/start` mới chạy (`test_menu_start_and_pause_freezes_timers`) | [01-menu.jpg](../proof/phase-2/ui/01-menu.jpg) | **Đạt** |
| DayIntro: Ngày + danh sách Má Tư đọc, tự chuyển sau 4 s hoặc khi bấm phím | `test_intro_holds_sim_then_auto_after_4s`, `test_key_skips_intro` (sim_tick = 0 trong lúc intro) | [02-day-intro.jpg](../proof/phase-2/ui/02-day-intro.jpg) | **Đạt** |
| HUD sáng: Máu, oxy (< 25% đổi màu + nhấp nháy), giờ (≤ 30 s đổi màu), độ sâu, giỏ theo loại, đã lấy/cần, hồi bắt | Chơi thử trên DaySim thật | [16-hud-gather-real-daysim-fps.jpg](../proof/phase-2/ui/16-hud-gather-real-daysim-fps.jpg) · [04-hud-gather-catch.jpg](../proof/phase-2/ui/04-hud-gather-catch.jpg) | **Đạt** |
| Gợi ý hái/cập bến/bắt; "Thủy quái!" + viền tím khi có quái gần; "Hết hơi!" khi oxy cạn | Lặn tới M1 trên DaySim thật: viền tím, chữ cảnh báo, toast `monster_hit` | [17-hud-monster-warning.jpg](../proof/phase-2/ui/17-hud-monster-warning.jpg) | **Đạt** |
| EveningIntro: số lượng nhập kho + món nấu được | `test_dock_evening_intro_uses_real_handover` (handover = `gather_end`, quán đứng yên khi chờ) | [05-evening-intro-fainted.jpg](../proof/phase-2/ui/05-evening-intro-fainted.jpg) | **Đạt** |
| HUD quán: đồng hồ ca, tiền ca, uy tín, món + kiên nhẫn từng bàn (< 25% đổi màu), tiến độ bếp / món chín, món đang cầm, kho khả dụng | Chơi thử nấu → bưng → dọn món; 2 bếp/4 bàn | [06-hud-quan.jpg](../proof/phase-2/ui/06-hud-quan.jpg) · [18-hud-quan-2bep-4ban.jpg](../proof/phase-2/ui/18-hud-quan-2bep-4ban.jpg) | **Đạt** |
| Pause Esc/P: làm mờ nền, Tiếp tục / Cài đặt / Về menu, đứng mọi timer kể cả Shop | Test HTTP: `state:"paused"`, `sim_tick`/`time_left` đứng, tick ngoài tăng | [07-pause.jpg](../proof/phase-2/ui/07-pause.jpg) | **Đạt** |
| DayResult: khách phục vụ/bỏ đi, tiền, boa, thay đổi uy tín | Gộp từ `served/paid/customer_left` | [08-day-result.jpg](../proof/phase-2/ui/08-day-result.jpg) | **Đạt** |
| Shop: mua oxygen/hp, buy_failed, cấp hiện ngay và áp từ Ngày kế | `test_full_day_result_shop_upgrade_and_summary` (D2 oxy 2700) | [09-shop.jpg](../proof/phase-2/ui/09-shop.jpg) | **Đạt** |
| Summary: tổng tiền, tổng điểm, uy tín, món bán chạy | cùng test trên (score = earned + 100·floor(rep)) | [10-summary.jpg](../proof/phase-2/ui/10-summary.jpg) | **Đạt** |
| Chữ không chân ≥ 18 px ở 1280×720 | Mọi cỡ chữ CSS và canvas `txt()` ≥ 18 px | `chonoi/web/index.html` | **Đạt** |
| Chơi thường ≥ 30 FPS ở 1280×720 | `window.__perf`, 300 khung, ca sáng có cá bơi + Cá Sấu | [fps.md](../proof/phase-2/fps.md) | **Đạt** — 60.0 FPS TB, khung chậm nhất 17.7 ms |
| Headless 1 Ngày ≤ 20 s | CP2 | [qa-report.md](../proof/phase-2/qa-report.md) | **Đạt** — 0.37 s |

## 4. Mở rộng và sáng tạo

| Mục | Phạm vi | Bằng chứng | Kết quả |
|---|---|---|---|
| Chợ Chú Sáu (vendor) | Chỉ cửa sổ chơi (lớp `live_day`), **không** khai ở `extensions` vì headless chưa hỗ trợ | `test_vendor_sell_and_buy_for_next_evening` · [14-shop-vendor-sell.jpg](../proof/phase-2/ui/14-shop-vendor-sell.jpg) | **Đạt (live)** |
| **Settings & âm thanh** (mục mở rộng không có mã trong Test Contract): Master/Music/SFX lưu giữa các lần mở | Client: menu/pause → Cài đặt, lưu `localStorage` khóa `chonoi.volume.v1`; kiểm bằng chỉnh thanh trượt, tải lại trang, giá trị giữ nguyên | Màn Cài đặt · `chonoi/web/index.html` | **Đạt** — tính là mục mở rộng bắt buộc của nhóm 5 người |
| Thời tiết, chuyện Má Tư kể, khách quen có tên | Chỉ client, không đổi event/luật (CP6, CP7 vẫn đạt) | [11](../proof/phase-2/ui/11-weather-rain-gather.jpg) · [12](../proof/phase-2/ui/12-quan-persona-rain.jpg) · [13](../proof/phase-2/ui/13-day-result-story.jpg) · [15](../proof/phase-2/ui/15-story-locked.jpg) | **Đạt** |

## Đánh giá

- **Đạt DoD Phase 2** trên cây làm việc: số chuẩn v1.1, cá/Cá Sấu/Máu/ngất, 2 bếp/4 bàn, vòng ngày D1–D5 với menu/pause/HUD, smoke tích hợp, regression 95/95.
- **Mở rộng:** Settings & âm thanh đạt (mục không có mã Test Contract, nên không khai `extensions`). Chợ Chú Sáu có mã `vendor` nhưng mới chạy ở cửa sổ chơi → chưa khai `extensions` cho tới khi DaySim headless hỗ trợ và có test.
- **Trước khi gắn tag:** merge nhánh TV5 vào main, chạy lại `python3 tools/qa_p2.py` trên commit đó, cập nhật hash trong qa-report rồi mới đẩy `phase-2`.
