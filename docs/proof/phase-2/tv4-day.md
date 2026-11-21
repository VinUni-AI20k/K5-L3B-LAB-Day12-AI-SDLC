# Phase 2 — Mode `day` (bản tạm TV4)

Nhánh `feat/p2-day`, tách từ `feat/p2-quan-day-menu` (TV3, `1cfdc46`) để dùng `day_dishes`. Ngày 2026-11-21, Windows, Python 3.12.

Chưa có TICKET-02 trong repo. Bản này dựng theo `game.contract.json` (`day_plan`, `shop`) và TV1_ACTION_PLAN_PHASE2 mục D4. Mọi tên sự kiện, tên trường và nút là giả định, ghi ở Q9 trong `docs/clarify.md`.

## Đã làm

- `chonoi/sim/day.py` — `DaySim`: vòng `day_start → day_plan → phase_start(gather)`.
  - `gather_end` thì mở Quán cùng tick, với kho = giỏ Gather (ngất thì kho rỗng) và `day_dishes` = món của `day_plan`.
  - `quan_end` thì mở Shop cùng tick.
  - Shop đóng thì phát `shop_end`, `day_end` và sang ngày sau.
  - Tiền, earned, uy tín mang qua các ngày. Quán mở ca với uy tín của Day. Kho dư bị bỏ sau Shop.
  - Shop tối đa `shop.max_ticks`. Mua `oxygen`/`hp` theo cấp và giá. Nâng cấp chỉ có hiệu lực từ ngày sau (`active_upgrades` chốt lúc `day_start`, Gather nhận tuning đã cộng nâng cấp).
  - Pause: `tick` vẫn tăng, `sim_tick`/`phase_tick`/đồng hồ đứng yên, snapshot `state: "paused"`. Resume thì chạy ngay bước đó.
- `chonoi/runner.py` (khung): `build_sim`/`Session`/`run` nhận `days`. `sim_tick`/`phase_tick` lấy từ sim nếu có, nên gather/quan giữ nguyên như v1.0.
- `chonoi/headless.py` (khung): bỏ lỗi "`day` chưa hỗ trợ", thêm `--days` (1..5, chỉ với `day`). `day` chưa nhận `--scenario`.
- `tests/test_smoke_p1.py`: bỏ `day` khỏi danh sách mode bị từ chối vì v1.1 đã hỗ trợ. Mode lạ (`river`) vẫn phải ra mã 2.
- `tests/test_day_mode.py`: 10 test.

## Lệnh và kết quả

```powershell
$env:PYTHONPATH='tests;.'; $env:PYTHONIOENCODING='utf-8'
python3 -m unittest discover -s tests
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 200000 --snapshot-every 600 --out day1.jsonl
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 200000 --snapshot-every 600 --out day5.jsonl
'{"frames":[{"tick":10,"pause":true},{"tick":11,"pause":false},{"tick":40,"pause":true},{"tick":41,"pause":false}]}' | Set-Content pause.json
python3 -m chonoi.headless --mode day --seed 1 --ticks 60 --inputs pause.json --snapshot-every 10 --out p.jsonl
```

| Kiểm | Kết quả |
|---|---|
| Unittest | `Ran 69 tests ... OK` (10 test mới trong `test_day_mode.py`) |
| `--days 1` | mã 0; thứ tự `day_start, day_plan, phase_start(gather), gather_end, phase_start(quan), quan_end, phase_start(shop), shop_end, day_end`; end `reason: days_complete`, 22 200 tick (10 800 + 10 800 + 600) |
| `--days 5` | mã 0; 111 000 tick |
| Chuyển pha cùng tick | `gather_end` và `phase_start(quan)` cùng tick; `quan_end` và `phase_start(shop)` cùng tick |
| Tất định | `--days 2 --seed 7` chạy hai lần trùng từng byte |
| Hiệu năng | một ngày headless < 20 s (test `test_one_day_headless_under_20s`) |
| Pause qua CLI | tick 20–40: `sim_tick` 10, `time_left_ticks` 10790, `state: paused`; tick 50: `sim_tick` 20 (resume ở tick 41 chạy ngay) |
| Nâng cấp | mua oxygen cấp 1 ở Shop ngày 1 thì `active_upgrades.oxygen` vẫn 0; ngày 2 là 1, Gather `oxygen_max` = 45 s; tuning gốc không đổi |
| Shop | không đủ tiền hoặc đã max cấp thì `buy_failed`; hết `max_ticks` thì đóng (`reason: time`) |
| Lỗi đầu vào | `--days 0`, `--days 6`, `--days` với gather, `--inventory-out` với day, `--scenario` với day: mã 2, không tạo output |

## Chưa làm / chờ

- Đổi tên sự kiện, trường, nút cho khớp TICKET-02 (Q9).
- `--scenario` cho mode `day`.
- Chơi trực tiếp (`chonoi.live`) mode `day` và HUD Shop/pause (phối hợp TV5).
- Q8: số lượng trong `day_plan.dishes` có giới hạn đơn không (TV3).
