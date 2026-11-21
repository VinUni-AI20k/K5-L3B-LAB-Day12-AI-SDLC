# Ma trận truy vết Phase 2

Nguồn yêu cầu: TICKET-02 / Test Contract v1.1 ([`docs/contracts/ticket-02-test-contract-v1.1.md`](../contracts/ticket-02-test-contract-v1.1.md)).
Tái tạo từ gốc repo: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (kết quả: [unittest.txt](../proof/phase-2/unittest.txt),
**122 test, OK**) và `bash docs/proof/phase-2/run_proof.sh` (kết quả: [proof.txt](../proof/phase-2/proof.txt)).

> Bằng chứng hiện chạy trên working tree **chưa commit** (dòng đầu `proof.txt` ghi `+dirty`). Khi gắn tag `phase-2`,
> Integrator chạy lại hai lệnh trên ở commit gắn tag và cập nhật `unittest.txt`, `proof.txt`.

## Số chuẩn, cá, Cá Sấu (lát 1–2, `tests/test_gather_p2.py`)

| AC | Yêu cầu | Test | Kết quả |
|---|---|---|---|
| AC-P2-01 | `contract_version` 1.1, tuning chuẩn, 6 nguyên liệu, 6 món, day_plan, shop | `test_ac_p2_01_*` | đạt |
| AC-P2-02 | Contract dữ liệu sai → mã 2 | `test_ac_p2_02_*` | đạt |
| AC-P2-03..06 | Cá bơi 1.5 m/s, `age_ticks`, đổi hướng theo seed ở bước 120·k, phản xạ mép/góc, giữ dải độ sâu | `test_ac_p2_03..06_*` | đạt |
| AC-P2-07..13 | `random_fish:false`, 8 đàn đầu ca khác điểm, sinh tất định, lịch 360·k, trần 12, clearance > 1 m, bỏ lượt | `test_ac_p2_07..13_*` | đạt |
| AC-P2-14..15 | Bắt theo vị trí trước khi bơi; cá kèo yield 2, nút kèo nèo N5/N6 | `test_ac_p2_14..15_*` | đạt |
| AC-P2-16..23 | Cá Sấu patrol/chase/exit, hit LIFO + bất tử 90, một hit/bước, không hit khi nông/recoil, recoil chặn mép | `test_ac_p2_16..23_*` | đạt |
| AC-P2-24..25 | Ngất do quái: mất giỏ, kho rỗng; ngạt xuyên bất tử, không rơi hàng | `test_ac_p2_24..25_*` | đạt |
| AC-P2-26..27 | M2 chỉ từ Ngày 3; tham số nâng cấp đang áp dụng | `test_ac_p2_26..27_*` | đạt |
| AC-P2-28..29 | Scenario gather v1.1 sai → mã 2; headless mặc định có `monsters[]`, `fish_spawned` | `test_ac_p2_28..29_*` | đạt |

## Quán (lát 3, `tests/test_quan_p2.py`)

| AC | Yêu cầu | Test | Kết quả |
|---|---|---|---|
| AC-P2-30 | B1 [2,8], B2 [5,8]; T1–T4 đúng tọa độ; 6 món | `test_ac_p2_30_*` | đạt |
| AC-P2-31 | Khách 120 + 900·k, bàn trống id nhỏ nhất (T1→T4 ở 120/1020/1920/2820) | `test_ac_p2_31_*` | đạt |
| AC-P2-32 | Hai bếp nấu song song; bếp lấy đơn reserved cũ nhất theo `order_tick` rồi id bàn | `test_ac_p2_32_*` | đạt |
| AC-P2-33 | Món mới (lẩu mắm): công thức, 12 s, giá 200 | `test_ac_p2_33_*` | đạt |
| AC-P2-34 | Quán độc lập dùng cả 6 món (theo seed) | `test_ac_p2_34_*` | đạt |
| AC-P2-35 | Có bàn mà không món nào nấu được → `no_dish` | `test_ac_p2_35_*` | đạt |
| AC-P2-53 | Trong `day`, lọc theo kế hoạch Ngày TRƯỚC khi lọc nguyên liệu | `test_day_p2.test_ac_p2_53_*` | đạt |

## Pause, vòng Ngày, Shop (lát 4, `tests/test_day_p2.py`)

| AC | Yêu cầu | Test / bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-40 | Pause trong quan: `paused`/`resumed`, state `paused`, sim_tick/phase_tick/time_left đứng yên, bỏ cạnh hành động, lịch khách lùi đúng số tick pause | `test_ac_p2_40_*` | đạt |
| AC-P2-41 | Pause trong gather: đồng hồ đứng yên, dòng end `state: paused` | `test_ac_p2_41_*` | đạt |
| AC-P2-42 | Pause trong Shop: timer 600 đứng yên, `buy` lúc pause bị bỏ | `test_ac_p2_42_*`; proof mục 4 (pause trong day: mọi mốc lùi 300 tick, sim_tick 22.200) | đạt |
| AC-P2-50 | `--mode day` công bố đúng kế hoạch D1–D5 (`day_plan` = contract), `days_complete` sau 5 Shop | `test_ac_p2_50_*` | đạt |
| AC-P2-51 | day_start → day_plan → phase_start(gather) ở tick 0; gather_end/quan_end/shop_end mang pha cũ, phase_start pha mới cùng tick; snapshot đổi pha `phase_tick:0`; vỏ event có `day`; snapshot có day/day_plan/upgrades/active_upgrades; Shop snapshot có stock + time_left_ticks | `test_ac_p2_51_*`; [day1.events.jsonl](../proof/phase-2/day1.events.jsonl) | đạt |
| AC-P2-52 | Ngất → quán vẫn mở cùng tick với kho rỗng | `test_ac_p2_52_*` | đạt |
| AC-P2-54 | money / earned / reputation mang qua Ngày; điểm = earned + 100·floor(uy tín) | `test_ac_p2_54_*` | đạt |
| AC-P2-60 | Mua đủ đúng giá; trừ money, giữ earned và điểm; thiếu tiền → `buy_failed funds` | `test_ac_p2_60_*` | đạt |
| AC-P2-61 | Đã tối đa → `max_level`; lệnh không hỗ trợ (`weapon`, `buy:ca_loc`) → `unknown`; tiền giữ nguyên | `test_ac_p2_61_*` | đạt |
| AC-P2-62 | Một buy xử lý trước cạnh shop_done cùng bước → `bought` rồi `shop_end(done)` | `test_ac_p2_62_*` | đạt |
| AC-P2-63..64 | Tự đóng sau 600 tick hoạt động `shop_end(time)`; buy ở bước cuối vẫn xử lý; shop_done ở bước cuối → `done` | `test_ac_p2_63/64_*` | đạt |
| AC-P2-65 | Cấp vừa mua hiện ngay trong `upgrades`, chỉ vào `active_upgrades` khi dựng Ngày kế; oxy 2.700 tick, Máu 4 từ Ngày 2 | `test_ac_p2_65_*`; proof mục 3 ([multiday-upgrades.txt](../proof/phase-2/multiday-upgrades.txt)) | đạt |
| AC-P2-70 | Scenario day sai (money > earned, thiếu earned, `quan.stock`/`quan.reputation`, ingredients sai, món lạ, cấp lạ/vượt, khóa lạ, khách món ngoài kế hoạch) và `--days` 0/6/x → mã 2, không ghi đầu ra | `test_ac_p2_70_*` | đạt |
| AC-P2-71 | `day.day_plan` ghi đè theo số Ngày, tính lại ingredients | `test_ac_p2_71_*` | đạt |
| AC-P2-72 | Mâu thuẫn trên kho thực lúc mở quán → mã 2, xóa đầu ra dở | `test_ac_p2_72_*` | đạt (xem C-P2-B05) |
| AC-P2-80 | Một Ngày không pause (22.200 tick) ≤ 20 s | `test_ac_p2_80_*`; proof mục 2: **0.76 s** | đạt |

## Smoke, regression (`tests/test_smoke_p2.py`, P1)

| AC | Yêu cầu | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-90 | Smoke tích hợp gather `--inventory-out` → quan `--inventory`, snapshot kho tick 0 khớp (gồm ca_keo, keo_neo) | `test_ac_p2_90_*`; [integration.txt](../proof/phase-2/integration.txt), `integration-*.jsonl`, `integration-kho.json` | đạt |
| AC-P2-91 | `day --days 1` trọn vòng, `days_complete`, `ticks 22200`, byte giống nhau khi chạy lại | `test_ac_p2_91_*`; proof mục 2 `BYTE-IDENTICAL OK` | đạt |
| Regression P1 | Test P1 còn hiệu lực đạt với số chuẩn | unittest.txt (toàn bộ test P1 OK) | đạt |

**Test P1 đã đổi vì luật mới (lý do ghi trong docstring từng test):**
- `test_quan_p1.test_ac_p1_22_*`: quán có 4 bàn, scenario không xóa được bàn mặc định → đặt sẵn khách ở T2–T4 để giữ tình huống "mọi bàn bận".
- `test_smoke_p1.test_gather_snapshot_has_gather_fields`: số đàn đầu ca = `fish_initial` (8) thay vì 6.
- `test_smoke_p1.test_con_03_*`: `--mode day` hợp lệ từ v1.1; `attack` là nút hợp lệ (bỏ qua khi chưa bật mở rộng) nên đổi sang nút lạ `fly`; thêm ca `--days` ngoài day → mã 2.
- `test_python_starter_units.test_catch_is_a_v10_button_and_attack_is_not`: `attack`/`pause` boolean được nhận; `jump` và `attack` sai kiểu vẫn mã 2.
- `test_gather_p1.test_ac_p1_18_*` (agent A): viết lại vì các đàn preset F1..F6 cố định của v1.0 không còn ở v1.1 (cá sinh theo seed và bơi).

## Chưa đạt / ngoài phạm vi headless (trung thực)

| Hạng mục DoD | Trạng thái |
|---|---|
| Menu chính, DayIntro (4 s), EveningIntro, DayResult, Summary, pause menu (Tiếp tục / Về menu), HUD v1.1 trong bản chơi | **chưa đạt** trong `chonoi.live` (chỉ có `--mode gather|quan`, chưa map Esc/P). Lõi pause đã có ở `Session` (dùng chung), `LiveInputs` nhận `pause`/`shop_done`/`buy` — còn thiếu phần giao diện. |
| ≥ 30 FPS ở 1280×720 | chưa đo |
| Mở rộng (Lao, vợt, rắn, cháy, Chợ, Sổ tay, Settings) | không làm (nhóm 3 người, không bắt buộc) |
