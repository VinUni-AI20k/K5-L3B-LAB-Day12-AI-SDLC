# Phase 2: smoke tích hợp, smoke `day`, Cá Sấu (QA `hungdt31`)

- **Commit kiểm:** `d4ce64e` = `main` `b83d2eb` + sửa payload `monster_hit`. Contract `1.1` · Python 3.14.4 / Linux.
- **Unit test:** 70/70 OK ([unittest.log](unittest.log)).
- **Cách sinh input:** dùng `tools/qa_autoplay.py`. Bot đọc snapshot rồi đuổi theo cá đang bơi, canh oxy, nấu ở nhiều bếp và mua nâng cấp ở Shop. Bằng chứng là kết quả chạy **headless** với file inputs đã sinh. `tools/qa_check_day.py` chạy lại cùng inputs trong tiến trình để kiểm những AC mà snapshot thưa không thấy.

## 1. Smoke tích hợp: `gather --inventory-out` → `quan --inventory`

```
python3 -m chonoi.headless --mode gather --seed 42 --ticks 10800 --snapshot-every 60 \
  --inputs docs/proof/phase-2/integration-gather-inputs.json \
  --inventory-out docs/proof/phase-2/integration-kho.json --out docs/proof/phase-2/integration-gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 10800 --snapshot-every 60 \
  --inventory docs/proof/phase-2/integration-kho.json \
  --inputs docs/proof/phase-2/integration-quan-inputs.json --out docs/proof/phase-2/integration-quan.jsonl
```

| Kiểm | Kết quả |
|---|---|
| Gather kết thúc | `reason: docked` tại tick 2692; 4 `gather`, 4 `fish_caught` (cá đang bơi), 7 `fish_spawned` (mỗi 360 tick) |
| Kho xuất | [integration-kho.json](integration-kho.json) = `{bong_dien_dien:1, bong_sung:2, ca_keo:2, ca_linh:3, ca_loc:2, keo_neo:1}`, đủ **6 nguyên liệu v1.1** |
| `stock` trong snapshot quan tick 0 == file kho | **Đạt** |
| Quan | 4 khách: `ca_loc_nuong_trui`, `ca_keo_nuong`, `canh_chua_ca_loc`, `goi_bong_sung`; 8 `no_dish` khi hết món làm được; `quan_end` `reason: time` |
| Tiền / uy tín / điểm | 60 + 70 + 90 + 40 = 260, boa 52 → **312**; uy tín 3.0 + 4 × 0.2 = **3.8**; điểm 312 + 100 × 3 = **612** |

## 2. Smoke `--mode day` (seed 1)

```
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 120000 --snapshot-every 120 \
  --inputs docs/proof/phase-2/day1-inputs.json --out docs/proof/phase-2/day1.jsonl
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 120000 --snapshot-every 120 \
  --inputs docs/proof/phase-2/day5-inputs.json --out docs/proof/phase-2/day5.jsonl
PYTHONPATH=. python3 tools/qa_check_day.py docs/proof/phase-2/day5-inputs.json   # → day5-checks.log
```

| Ngày | Cá Sấu | Kho bàn giao | Thu ca | Mua ở Shop | Đầu Ngày kế: oxy / Máu tối đa |
|---|---|---|---|---|---|
| D1 | M1 | `ca_loc 3, bong_sung 6` (đúng kế hoạch) | 360 | `oxygen` cấp 1 (200) | D2: **2700** / 3 |
| D2 | M1 | `ca_loc 2, ca_linh 6, bong_dien_dien 2` | 432 | `hp` cấp 1 (250) | D3: 2700 / **4** |
| D3 | M1, **M2** | 2 lần bị hit, sau đó vẫn cập bến | 480 | `oxygen` cấp 2 (400) | D4: **3600** / 4 |
| D4 | M1, M2 | 2 lần bị hit | 432 | `hp` cấp 2 (500) | D5: 3600 / **5** |
| D5 | M1, M2 | cập bến | 456 | (đã tối đa) | n/a |

Kết thúc: `reason: days_complete`, `days_completed: 5`, money 810, earned 2160, reputation 5, score 2660.

### Cá Sấu (4 lần `monster_hit` trong day5, kiểm bởi [day5-checks.log](day5-checks.log))

| Tick | Con | Máu | Số món trong giỏ | `lost` (LIFO) | Đạt |
|---|---|---|---|---|---|
| 31228 | M1 | 4 → 3 | 5 | `ca_loc, bong_sung` (floor 5/2 = 2) | ✅ |
| 31318 | M1 | 3 → 2 | 5 | `ca_keo, ca_keo` (đúng 90 tick sau cú hit trước) | ✅ |
| 46848 | M2 | 4 → 3 | 9 | 4 món | ✅ |
| 47688 | M1 | 3 → 2 | 10 | 5 món | ✅ |

Mỗi dòng đều kiểm: payload đúng `{monster_id, hp, lost, pos}`, `lost` đúng các món cuối giỏ theo thứ tự mới nhất trước, Máu −1, `invuln_ticks` được đặt 90, người chơi ở d ≥ 10.

## 3. Hiệu năng & tất định

- `day --days 1` 0.46 s; `--days 5` 1.26 s; `day` không input (22 200 tick) < 1 s. Mức yêu cầu là ≤ 20 s mỗi Ngày.
- Chạy lại gather, quan, day1, day5 rồi `cmp`: giống từng byte.

## 4. Ghi nhận

- Khi uy tín chạm trần, JSON in `"reputation":5` (int, do `reputation_max: 5` trong contract) thay vì `5.0`. Giá trị đúng; chỉ lệch nếu máy chấm so byte với bản tham chiếu. Cần báo lát `quan`.
- `snapshot()` trả tham chiếu tới list sống (`hold`, …). Headless không bị ảnh hưởng vì ghi JSON ngay, nhưng code đọc snapshot rồi giữ lại (UI, công cụ) phải tự `deepcopy`.
