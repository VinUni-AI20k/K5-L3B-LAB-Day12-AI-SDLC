# Bằng chứng tích hợp gather → file kho → quan (Phase 1)

Người chạy: TV3 (Tiberu2611) · nhánh `Manh` sau khi gộp `origin/main` (gather lát 1–2 của TV1, lát 3 của TV2) · Python 3.15.2 (Windows).
Lệnh dùng `python3 -m chonoi.headless` = `headless_cmd` trong `game.contract.json` (trên máy Windows này `python3` chạy từ một venv tạm,
vì `python3` mặc định là alias của Microsoft Store).

## 1. Smoke hai tiến trình (PRD-0 mục G) — ĐẠT

```bash
P=docs/proof/phase-1/integration
python3 -m chonoi.headless --mode gather --seed 42 --scenario $P/dock.json --inputs $P/dock-inputs.json \
  --ticks 1 --out $P/gather.jsonl --inventory-out $P/catch.json        # exit 0
python3 -m chonoi.headless --mode quan --seed 42 --inventory $P/catch.json --ticks 0 --out $P/quan.jsonl   # exit 0
```

| Kiểm | Kết quả thật |
|---|---|
| `gather_end` trong [gather.jsonl](gather.jsonl) | `{"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}` |
| [catch.json](catch.json) | `{"items":{"bong_sung":2,"ca_loc":1}}` — khớp `inventory` trong `gather_end` |
| `stock` ở snapshot tick 0 của [quan.jsonl](quan.jsonl) | `{"bong_sung":2,"ca_loc":1}` — đúng file tiến trình đầu ghi |

## 2. Chơi nối đủ 3 lát bằng headless (thư mục [e2e/](e2e/)) — ĐẠT

Gather thật (lát 1–2, TV1) → file kho → quán với khách tự sinh (lát 3, TV2) → bếp/bưng/phục vụ/trả tiền (lát 4, TV3).

```bash
E=docs/proof/phase-1/integration/e2e
python3 -m chonoi.headless --mode gather --seed 1 --scenario $E/gather-scenario.json --inputs $E/gather-inputs.json \
  --ticks 2000 --snapshot-every 100 --out $E/gather.jsonl --inventory-out $E/catch.json     # exit 0
python3 -m chonoi.headless --mode quan --seed 1 --inventory $E/catch.json --inputs $E/quan-inputs.json \
  --ticks 10800 --snapshot-every 1200 --out $E/quan.jsonl                                     # exit 0
```

| Tick | Event | Lát |
|---|---|---|
| gather 1 | `fish_caught` F1 `ca_loc` ×1 (lặn ở d = 5) | 2 |
| gather 348 | `surface` (bơi lên, về bến) | 1 |
| gather 511 | `gather_end` `docked`, kho `{"ca_loc":1}` → [e2e/catch.json](e2e/catch.json) | 2 |
| quan 120 | `customer_arrived` C1 gọi `ca_loc_nuong_trui` (món duy nhất đủ nguyên liệu) | 3 |
| quan 126 | `cook_started` B1, `items:["ca_loc"]`, `base_price:60` | 4 |
| quan 486 / 489 | `dish_ready` (đúng 360 tick = `cook_s` 6) / `dish_picked` | 4 |
| quan 639 | `served`, `patience_ticks_left:3081` (≥ 50%) → `tip:12` | 4 |
| quan 1239 | `paid` `finished_eating`, `amount:72` (đúng 600 tick ăn) | 4 |
| quan 1920 … 10020 | `no_dish` mỗi 900 tick (kho đã hết) | 3 |
| quan 10800 | `quan_end`, `end`: `money 72, earned 72, reputation 3.2, score 372` | 3+4 |

Dòng `end` trùng từng số với ví dụ `end` trong PRD-0 mục E. Chạy lại cùng lệnh cho `quan.jsonl` giống từng byte.

## 3. Bộ test tự động — 93/93 ĐẠT

Log đầy đủ: [test-run.txt](test-run.txt) (`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → `Ran 93 tests … OK`, không skip).
Gồm `test_smoke_p1` (giảng viên), `test_gather_p1` (TV1), `test_quan_lat3` (TV2), `test_quan_kitchen` + `test_quan_service` +
`test_integration_gather_quan` (TV3).

Test tích hợp [`tests/test_integration_gather_quan.py`](../../../../tests/test_integration_gather_quan.py) (hộp đen qua `headless_cmd`):

| Test | Kiểm điều gì (PRD-0) | Kết quả |
|---|---|---|
| `test_inventory_file_matches_gather_end_and_quan_stock` | G: file = `gather_end.inventory`, quán nhận đúng stock; tiền/uy tín đầu lượt | đạt |
| `test_empty_hold_gives_empty_inventory_and_empty_stock` | G: kho rỗng `{"items":{}}` | đạt |
| `test_quan_cooks_and_sells_with_ingredients_from_gather` | Hàng mang về được nấu → bưng → phục vụ → trả tiền; stock về rỗng | đạt |
| `test_time_out_writes_inventory` | F/G: hết giờ → `time`, ghi kho, dừng sớm | đạt |
| `test_tick_limit_does_not_create_or_overwrite_inventory` | G: chạm `--ticks` trước `gather_end` không tạo / không ghi đè file | đạt |
| `test_faint_writes_empty_inventory` | G: ngất → kho rỗng (chạy thật từ khi có lát 1 của TV1) | đạt |
| `test_deterministic_inventory_and_jsonl_bytes` | E: cùng seed → file kho và JSONL giống từng byte | đạt |
| `test_quan_rejects_bad_inventory_exit_2` | G: kind lạ, số âm, số thực, khóa gốc thừa, thiếu `items` → mã 2, không ghi JSONL | đạt |
| `test_inventory_and_scenario_stock_together_exit_2` | D: khai cả `quan.stock` và `--inventory` → mã 2 | đạt |

## Ghi chú trung thực
- Chạy trên Windows; CI của repo chạy cùng lệnh trên Ubuntu với `python3` thật.
- JSONL trong `e2e/` dùng `--snapshot-every` thưa để file nhỏ; event và dòng `end` không phụ thuộc cờ này.
- `.gitignore` bỏ `*.jsonl`, các file JSONL bằng chứng được thêm bằng `git add -f`.
