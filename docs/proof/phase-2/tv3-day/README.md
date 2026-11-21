# Bằng chứng Phase 2 — phần TV3 (`--mode day`, Shop, Pause, burn)

Người chạy: TV3 (`Tiberu2611`) · bản ghép `main` (contract v1.1, PR #10) + nhánh `Manh` · Python 3.15.2 (Windows, `python3` từ venv tạm).
Lệnh = `headless_cmd` trong `game.contract.json` (`python3 -m chonoi.headless`).

## 1. Một Ngày không input (`--days 1`) — ĐẠT
```bash
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 30000 --snapshot-every 1200 --out day1-noinput.jsonl
```
| Tick | Event |
|---|---|
| 0 | `day_start`, `day_plan` D1 `{ca_loc_nuong_trui:3, goi_bong_sung:3}` → `{ca_loc:3, bong_sung:6}`, `phase_start(gather)` |
| 10800 | `gather_end(time)` → `phase_start(quan)` cùng tick |
| 21600 | `quan_end(time)` → `phase_start(shop)` cùng tick |
| 22200 | `shop_end(time)` (600 tick) → `end` `days_complete`, `days_completed: 1` |

Một Ngày không pause = **22.200 tick**, chạy **0,93 s** (yêu cầu ≤ 20 s). File: [day1-noinput.jsonl](day1-noinput.jsonl).

## 2. Hai Ngày, mua nâng cấp, pause trong Shop — ĐẠT
Scenario [upgrade-scenario.json](upgrade-scenario.json) (tiền đầu kỳ 200, cập bến ngay, ca quán rút ngắn) + inputs [upgrade-inputs.json](upgrade-inputs.json):
```bash
python3 -m chonoi.headless --mode day --days 2 --seed 1 --scenario upgrade-scenario.json --inputs upgrade-inputs.json \
  --ticks 400 --snapshot-every 50 --out day2-upgrade.jsonl
```
| Tick | Event |
|---|---|
| 1 | `gather_end(docked)` → `phase_start(quan)` |
| 61 | `quan_end` (money 200, earned 200) → `phase_start(shop)` |
| 71 / 101 | `paused` / `resumed` — 30 tick pause, `sim_tick` 370 trên 400 tick ngoài |
| 102 | `bought {upgrade: oxygen, level: 1, price: 200, money: 0}` (trừ money, earned giữ 200) |
| 103 | `shop_end(done)` → `day_start`, `day_plan` D2, `phase_start(gather)` của **Ngày 2** cùng tick |

Snapshot gather Ngày 2: `active_upgrades {"oxygen": 1}`, `oxygen_max_ticks 2700` (45 s). Chạy lại cùng lệnh **giống từng byte**.
File: [day2-upgrade.jsonl](day2-upgrade.jsonl).

## 3. Test
- [test-run.txt](test-run.txt): `test_day` (19), `test_pause_inputs` (8), `test_quan_burn` (10, burn bật `burn_s: 20`), `test_quan_p2_kitchen` (10), `test_quan_invariants`, `test_quan_kitchen`, `test_quan_service`, `test_smoke_p1`.
- [full-suite.txt](full-suite.txt): toàn bộ suite trên bản ghép — `OK (skipped=11)` (11 test v1.2 độ tươi chưa tới phase).

## Ghi chú trung thực
- Chạy trên bản ghép tạm vì lệnh merge `origin/main` vào `Manh` bị công cụ chặn; ba thay đổi chạm file đã đổi trên `main`
  (`chonoi/scenario.py` khối day, `game.contract.json` bật burn, `tests/test_smoke_p1.py` test_con_03) nằm ở patch chờ áp sau merge.
- `test_smoke_p1.test_con_03` được cập nhật vì luật v1.1: `day` là mode hợp lệ; mode lạ (`river`, `night`) vẫn mã 2.
