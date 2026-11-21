# Ma trận truy vết Phase 2

> Kiểm chứng trên nhánh nền `mKhaiTruong/contract-v1.1` @ `dafe2ee` (PR #14), 2026-11-21, Windows 11 + Python 3.12 (`.venv`, shim `python3`). Máy chấm chạy Linux.
> Bằng chứng: [`docs/proof/phase-2/`](../proof/phase-2/). Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → **132/134** ([`tests.txt`](../proof/phase-2/tests.txt)); 2 fail chờ lát cá (AC-P2-03).
> **Chưa phải commit bàn giao**: cập nhật lại bảng này khi lát gather của Phong vào nhánh nền và PR #14 merge vào `main`.

## Số chuẩn + gather

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 `contract_version: "1.1"`, số chuẩn mục 1, dải hợp lệ được kiểm lúc nạp | so từng số với TICKET-02; script tính lại `ingredients` D1–D5 và điểm sinh | `game.contract.json`, `chonoi/contract.py`; D1–D5 khớp (9/10/12/9/10 ô), 36 cặp loài–vị trí / 30 vị trí | đạt |
| AC-P2-02 Đủ 6 nguyên liệu, 6 món theo dữ liệu, nút N5/N6 | smoke tích hợp | [`integration.txt`](../proof/phase-2/integration.txt): kho có `ca_keo`, `keo_neo`; khách gọi `ca_keo_nuong` | đạt |
| AC-P2-03 Cá bơi 1.5 m/s, đổi hướng 120 bước, phản xạ mép; 8 đàn đầu ca theo seed, sinh thêm mỗi 360 tick, trần 12 | test hộp đen | — (`test_l2_16`, `test_gather_snapshot_has_gather_fields` còn fail) | **chưa** (lát Phong đang làm) |
| AC-P2-04 Cá Sấu: patrol 1 m/s, chase 3 m/s (d ≥ 10, ≤ 10 m), thoát > 16 m / d < 10, chạm ≤ 1.5 m, recoil 60 bước × 2/60 m, M2 từ Ngày 3 | unit test module | `tests/test_monsters.py` (11 test), `chonoi/sim/monsters.py` | **đạt một phần**: module đúng, **chưa nối vào `gather.py`** (Phong) |
| AC-P2-05 Chạm: −1 Máu, mất floor(n/2) LIFO, bất tử 90; ngất do quái → kho rỗng, vẫn mở quán | unit test (`apply_hit`) + `test_day.test_faint_gives_empty_stock` (ngất do ngạt) | `test_monsters.test_apply_hit_lifo_and_recoil` | **đạt một phần**: chờ nối vào gather (`monster_hit`, `faint cause: "monster"`) |
| AC-P2-06 Scenario v1.1 → mã 2 (`monsters[]`, `age_ticks`, `invuln_ticks`, khối `day`, cấm `quan.stock`/`quan.reputation` trong day) | test | `tests/test_scenario_v11.py` (10), `test_day.Scenario` (3), `test_day.PlanAndOrder` | đạt |

## Quán + vòng ngày

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-07 2 bếp / 4 bàn, bàn trống id nhỏ nhất | smoke + test | `integration.txt` (C1→T1, C2→T2, C3→T3), `tests/test_quan.py` | đạt |
| AC-P2-08 Smoke tích hợp `gather --inventory-out` → `quan --inventory`, tất định | 2 tiến trình, so byte | `integration.txt`: snapshot quán tick 0 `stock` **giống hệt** `catch.json`; chạy lại 3 file giống từng byte | đạt |
| AC-P2-09 `--mode day`: `day_start → day_plan → phase_start(gather)` → `gather_end` → `phase_start(quan)` cùng tick → `quan_end` → `phase_start(shop)` → `shop_end` → Ngày kế; event tick 0 trước snapshot | smoke 2 Ngày + test | [`day-multiday.txt`](../proof/phase-2/day-multiday.txt); `test_day.DayFlow`, `test_start_events_written_before_tick0_snapshot` | đạt |
| AC-P2-10 Kế hoạch D1–D5 công bố đúng; quán trong day chỉ gọi món của kế hoạch | test + smoke | `day-multiday.txt` (D1, D2 `day_plan`), `test_quan_menu_filtered_by_plan` | đạt |
| AC-P2-11 Tiền, earned, uy tín, cấp giữ qua Ngày; oxy/Máu hồi đầy theo cấp đang áp dụng | smoke 2 Ngày | `day-multiday.txt`: Ngày 2 `oxygen_max_ticks 2700`, `hp 4/4`, money 550 / earned 1000 | đạt |
| AC-P2-12 Shop: `bought` trừ money giữ earned; `buy_failed` funds / max_level / unknown; buy trước `shop_done`; tự đóng sau 600 tick; cấp hiện ngay, hiệu lực từ Ngày kế | smoke + test | `day-multiday.txt` (`bought` ×3, `buy_failed` funds + unknown; `upgrades` đổi ngay, `active_upgrades` đổi ở Ngày 2); `test_day.Shop` (8 test) | đạt |
| AC-P2-13 Pause: chỉ tick ngoài tăng, `paused`/`resumed`, timer (kể cả Shop) đứng yên, resume chạy ngay | smoke + test | `day-multiday.txt` phần "Kiểm thêm"; `test_day.Pause` (3 test) | đạt |
| AC-P2-14 `--days 1..5` (mặc định 1), dòng `end` có `days_completed`, `reason: days_complete` | test + smoke | `test_day.Cli` (3 test); `day-multiday.txt` dòng end | đạt |
| AC-P2-15 Headless một Ngày ≤ 22.200 tick chạy ≤ 20 s | đo thời gian | `day-multiday.txt`: 2 Ngày (21.609 tick) **0.37 s** trên máy dev | đạt (chưa đo trên Linux) |

## DoD còn lại

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-16 Regression P1 với số chuẩn, test đổi có ghi lý do | toàn bộ test | `tests.txt` 132/134; lý do đổi test ghi trong commit (`5039214` bỏ `two_tables`, `8876859` B2 → B9) | **đạt một phần**: 2 test cá cần sửa cùng lát Phong |
| AC-P2-17 Menu chính, DayIntro/EveningIntro/DayResult/Summary, pause menu, HUD v1.1 (≥ 18 px, 1280×720, ≥ 30 FPS) | chơi thử | — | **chưa** (ưu tiên headless trước) |
| AC-P2-18 Ghi chép: clarify, ai-usage-log, retro | đọc | `docs/clarify.md` #11–#14, `docs/retro.md` Phase 2 | đạt một phần (ai-usage-log P2 chưa đủ người) |
| AC-P2-19 Tag `phase-2` trỏ tới commit bàn giao trên `main` | `git tag` | — | chưa |

## Đánh giá ngắn
- **Đạt:** contract v1.1, scenario v1.1, quán 2 bếp/4 bàn/6 món, toàn bộ luồng `day` + Shop + pause, smoke tích hợp tất định, hiệu năng headless.
- **Chưa / một phần:** cá bơi/sinh và nối Cá Sấu vào gather (lát Phong); UI menu/HUD v1.1.
- **Rủi ro:** giả định chưa xác nhận (`recoil_dist` là tổng quãng, vị trí `day_plan`/`shop` trong `tuning`, cách rút loài cá theo trọng số); test ẩn có thể chấm khác.
