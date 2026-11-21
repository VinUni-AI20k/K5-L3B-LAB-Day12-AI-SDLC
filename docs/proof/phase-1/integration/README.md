# Bằng chứng tích hợp gather → file kho → quan (Phase 1)

Người chạy: TV3 (Tiberu2611) · nhánh `Manh` · dựa trên commit `1a8d67b` + test tích hợp mới · Python 3.15.2 (Windows).
Lệnh dùng `python -m chonoi.headless` (cùng module với `headless_cmd` trong `game.contract.json`; trên máy này `python3` là alias của Store).

## 1. Smoke hai tiến trình (PRD-0 mục G) — ĐẠT

```bash
P=docs/proof/phase-1/integration
python -m chonoi.headless --mode gather --seed 42 --scenario $P/dock.json --inputs $P/dock-inputs.json \
  --ticks 1 --out $P/gather.jsonl --inventory-out $P/catch.json        # exit 0
python -m chonoi.headless --mode quan --seed 42 --inventory $P/catch.json --ticks 0 --out $P/quan.jsonl   # exit 0
```

| Kiểm | Kết quả thật |
|---|---|
| `gather_end` trong [gather.jsonl](gather.jsonl) | `{"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}` |
| [catch.json](catch.json) | `{"items":{"bong_sung":2,"ca_loc":1}}` — khớp `inventory` trong `gather_end` |
| `stock` ở snapshot tick 0 của [quan.jsonl](quan.jsonl) | `{"bong_sung":2,"ca_loc":1}` — đúng file tiến trình đầu ghi |

## 2. Test tích hợp tự động — 8 đạt, 1 chờ lát 1

File: [`tests/test_integration_gather_quan.py`](../../../../tests/test_integration_gather_quan.py) (hộp đen qua `headless_cmd`). Log đầy đủ: [test-run.txt](test-run.txt) (40 test, OK, skipped=1).

| Test | Kiểm điều gì (PRD-0) | Kết quả |
|---|---|---|
| `test_inventory_file_matches_gather_end_and_quan_stock` | G: file = `gather_end.inventory`, quán nhận đúng stock; tiền/uy tín đầu lượt | đạt |
| `test_empty_hold_gives_empty_inventory_and_empty_stock` | G: kho rỗng `{"items":{}}` | đạt |
| `test_quan_cooks_and_sells_with_ingredients_from_gather` | Hàng mang về được nấu → bưng → phục vụ → trả tiền; stock về rỗng | đạt |
| `test_time_out_writes_inventory` | F/G: hết giờ → `time`, ghi kho, dừng sớm | đạt |
| `test_tick_limit_does_not_create_or_overwrite_inventory` | G: chạm `--ticks` trước `gather_end` không tạo / không ghi đè file | đạt |
| `test_deterministic_inventory_and_jsonl_bytes` | E: cùng seed → file kho và JSONL giống từng byte | đạt |
| `test_quan_rejects_bad_inventory_exit_2` | G: kind lạ, số âm, số thực, khóa gốc thừa, thiếu `items` → mã 2, không ghi JSONL | đạt |
| `test_inventory_and_scenario_stock_together_exit_2` | D: khai cả `quan.stock` và `--inventory` → mã 2 | đạt |
| `test_faint_writes_empty_inventory` | G: ngất → kho rỗng | **chờ lát 1** (sim/gather chưa có oxy/ngạt; test tự skip, sẽ chạy khi lát 1 xong) |

## Còn thiếu / ghi trung thực
- Đã gộp lát 3 (nhánh `tv2`) vào `Manh`: toàn bộ 84 test xanh (gồm `test_quan_lat3` và `test_smoke_p1`, chạy bằng
  `python3` trong venv tạm vì `python3` của máy là alias Store). Bảng ở mục 2 và `test-run.txt` là lần chạy trước khi gộp.
- Ca quán đầy đủ có khách tự sinh, không điều khiển (`--seed 5`, kho `{"ca_loc":3,"bong_sung":4,"ca_linh":3,"bong_dien_dien":1}`):
  khách đến ở tick 120, 3720, 7320; hai khách đầu rời vì hết kiên nhẫn (uy tín 3.0 → 2.5 → 2.0), khách cuối rời `closing`
  không trừ uy tín; `end` score 200; chạy hai lần giống từng byte.
- Smoke trong `tests/test_smoke_p1.py` gọi `python3` nên chưa chạy được trên máy Windows này; CI (Ubuntu) chạy được.
