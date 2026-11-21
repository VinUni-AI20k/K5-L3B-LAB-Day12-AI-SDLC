# Phase 3: smoke kho cá thể, smoke `day`, regression (QA `hungdt31`)

- **Commit kiểm:** `32883d0` = `main` `39be0e1` + 2 bản sửa và phần chuyển test (nhánh `test/p3-qa-changelog-v2`). Contract `1.2` · Python 3.14.4 / Linux.
- **Unit test:** 86/86 OK ([unittest.log](unittest.log)). Trên `main` `39be0e1` trước khi chuyển fixture: 20/78 đỏ.
- Input sinh bằng `tools/qa_autoplay.py`. Bằng chứng là kết quả chạy **headless** với file inputs đó.

## 1. Smoke 2 tiến trình kho cá thể: `gather --inventory-out` → `quan --inventory`

```
python3 -m chonoi.headless --mode gather --seed 42 --ticks 10800 --snapshot-every 60 \
  --inputs docs/proof/phase-3/integration-gather-inputs.json \
  --inventory-out docs/proof/phase-3/integration-kho.json --out docs/proof/phase-3/integration-gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 10800 --snapshot-every 60 \
  --inventory docs/proof/phase-3/integration-kho.json \
  --inputs docs/proof/phase-3/integration-quan-inputs.json --out docs/proof/phase-3/integration-quan.jsonl
python3 tools/qa_check_quan_prices.py docs/proof/phase-3/integration-quan.jsonl   # → integration-prices.log
```

| Kiểm | Kết quả |
|---|---|
| Gather | `docked` tại tick 2692. [integration-kho.json](integration-kho.json) có **11 cá thể `I1..I11`** đủ 6 loại; một đàn 3 cá linh thành 3 cá thể cùng độ tươi |
| Snapshot quan tick 0: `stock` == `items` trong file kho (cùng `id`, cùng `fresh`) | **Đạt** |
| Giá chốt theo độ tươi (4 món) | **Đạt**: [integration-prices.log](integration-prices.log) |

| Món | Niêm yết | avg fresh | `base_price` | Boa | Thu |
|---|---|---|---|---|---|
| ca_loc_nuong_trui (I8) | 60 | 84.82 | 50 | 10 | 60 |
| ca_keo_nuong (I6, I7) | 70 | 77.10 | 53 | 10 | 63 |
| canh_chua_ca_loc (I1, I5) | 90 | 70.87 | 63 | 12 | 75 |
| goi_bong_sung (I9, I10) | 40 | 76.06 | 30 | 6 | 36 |

Tổng 234, uy tín 3.8, điểm 534. Với cùng seed ở v1.1 tổng là 312: đây là tác động mong đợi của việc chốt giá theo độ tươi. `items` trong `cook_started` sắp theo `(kind, id)`.

## 2. Smoke `--mode day` (seed 1)

```
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 120000 --snapshot-every 120 \
  --inputs docs/proof/phase-3/day5-inputs.json --out docs/proof/phase-3/day5.jsonl
PYTHONPATH=. python3 tools/qa_check_day.py docs/proof/phase-3/day5-inputs.json   # → day5-checks.log
python3 tools/qa_check_quan_prices.py docs/proof/phase-3/day5.jsonl              # → day5-prices.log
```

| Kiểm | Kết quả |
|---|---|
| Kho mở quán == `gather_end.inventory` (gồm cả `fresh`, nghĩa là chuyển pha không hao thêm), cả 5 Ngày | Đạt ([day5-checks.log](day5-checks.log)) |
| Id họ `I` nối tiếp xuyên Ngày: D1 `I1..I9`, D2 `I10..I19`, D3 `I20..I35`, D4 `I36..I56`, D5 `I57..I68`; không trùng | **Đạt sau bản sửa `32883d0`** ([day5-ids.log](day5-ids.log)). Trước đó cả 5 Ngày đều bắt đầu từ `I1` |
| 23 lần `cook_started` đúng `floor(giá × avg_fresh / 100)`, `items` sắp `(kind, id)`, boa tính trên giá chốt | Đạt ([day5-prices.log](day5-prices.log)) |
| `spoiled` trong quán: `I40` (ca_linh, `location: "stock"`) ở Ngày 4 | Đạt: phát một lần |
| Cá Sấu: 4 cú hit, `lost` là cá thể theo LIFO (vd. `I14, I13, I12, I11, I10`) | Đạt |
| Khách chỉ gọi món trong `day_plan`; Shop; nâng cấp áp từ Ngày kế; `days_complete` | Đạt |
| Kết thúc | money 180, earned 1530, reputation 5, score 2030, `days_completed: 5` |

## 3. Schema v1.2: kho đếm và dạng sai → mã 2 ([schema-exit2.log](schema-exit2.log))

Kho đếm `{"items": {"ca_loc": 1}}`, thiếu `fresh`, `fresh: 101`, `id` trùng, `hold: ["ca_loc"]` đều ra **mã 2**. Kho cá thể hợp lệ ra mã 0.

## 4. Hiệu năng & tất định

- `day --days 1` 0.72 s; `--days 5` 2.67 s (≤ 20 s mỗi Ngày).
- Chạy lại gather, quan (`integration`), day1, day5 rồi `cmp`: giống từng byte.
