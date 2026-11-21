# Chơi thử quán với kho thật (Phase 1.4 — minhphuong150505 + phuthaitran)

Kiểm trên nhánh `p1/lat4-phuthaitran` sau khi gộp `origin/main` (9ad3a3e). Liên quan AC-P1-06, 07, 08, 09, 10.

## Lệnh chạy lại (từ gốc repo)

```bash
P=docs/proof/phase-1/quan-playtest
# 1. Gather thật ghi kho (smoke mục G, seed 42) -> kho.json = {"items":{"bong_sung":2,"ca_loc":1}}
python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --scenario $P/dock.json \
  --inputs $P/dock-inputs.json --inventory-out $P/kho.json --out $P/gather.jsonl
# 2. Quán nạp kho đó, chơi cả ca bằng input đã ghi (đi lại + E)
python3 -m chonoi.headless --mode quan --seed 42 --ticks 10800 --inventory $P/kho.json \
  --inputs $P/quan-inputs.json --snapshot-every 600 --out $P/quan.jsonl
# 3. Trên trình duyệt: PYTHONUTF8=1 python3 -m chonoi.live --mode quan --seed 42 --port 8765 --inventory $P/kho.json
```

`quan-inputs.json` do một bot nhỏ sinh ra: bot chỉ đọc snapshot như UI, đi tới bếp/bàn rồi bấm E (cạnh lên), phục vụ mọi khách **trừ khách thứ 2** để khách đó hết kiên nhẫn.

## Kết quả headless (`quan.jsonl`)

| tick | event | ghi chú |
|---|---|---|
| 120 | `customer_arrived` C1 `ca_loc_nuong_trui` | khách đầu ở `first_customer_tick` |
| 207 → 567 | `cook_started` (`items:["ca_loc"]`, 60) → `dish_ready` | 360 tick = `cook_s` 6 |
| 568 → 678 | `dish_picked` → `served` (kiên nhẫn 3042/3600, boa 12) | |
| 1278 | `paid` 72 `finished_eating` | đúng 600 tick sau `served`; uy tín 3.2 |
| 1020 | (không event) | bàn đang có khách ăn → bỏ lượt |
| 1920 | `customer_arrived` C2 `goi_bong_sung` | bot cố ý bỏ mặc |
| 5520 | `customer_left` C2 `patience`, uy tín 2.7 | 1920 + 3600; nhả giữ chỗ |
| 5520 | `customer_arrived` C3 `goi_bong_sung` | bàn trống ngay trong bước, dùng lại nguyên liệu vừa nhả |
| 5629 → 6579 | nấu → bưng → `served` (boa 8) → `paid` 48 | uy tín 2.9 |
| 7320, 8220, 9120, 10020 | `no_dish {}` | hết kho |
| 10800 | `quan_end` money 120, earned 120, reputation 2.9 | `end` score 320 = 120 + 100 × floor(2.9) |

- Chạy lại cùng seed và cùng đầu vào: `cmp` giống từng byte (`determinism.txt`).
- `live-log.txt`: chơi trên `chonoi.live` thật qua `GET /state` / `POST /input` (cùng API trình duyệt dùng) tới tick 5600. Chuỗi event giống headless; tick lệch vài đơn vị vì input gửi theo đồng hồ thật.
- `test-log.txt`: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → 134 test OK.

## Lỗi thấy khi chơi và đã sửa nhanh

1. `no_dish` phát `{"table_id":...}`, PRD-0 mục E yêu cầu `{}` → sửa (test lát 3 đổi assert theo PRD).
2. `customer_arrived` thiếu `order_id` (PRD-0 mục E) → thêm, giữ `customer_id`/`reserved` cho hợp đồng nhóm.
3. HUD in `st.dish` là object → bếp hiện `[object Object]`; nay hiện `dish_id`.

Chưa làm: ảnh chụp HUD (AC-P1-11, phần của RachalHys).
