# Phase 2: smoke tích hợp và smoke `day` (QA `hungdt31`)

- **Commit kiểm:** `4edc10c` (main sau PR #14) · contract `1.1` · Python 3.14.4 / Linux.
- **Unit test:** 65/65 OK ([unittest.log](unittest.log)).
- **Cách sinh input:** dùng `tools/qa_autoplay.py`. Bot đọc snapshot rồi đuổi theo cá đang bơi, canh oxy, nấu ở nhiều bếp và mua nâng cấp ở Shop. Bằng chứng là kết quả chạy **headless** với file inputs đã sinh, không phải bot.

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
| `stock` snapshot quan tick 0 == file kho | **Đạt** (so khớp tuyệt đối) |
| Quan | 4 khách: phục vụ `ca_loc_nuong_trui`, `ca_keo_nuong`, `canh_chua_ca_loc`, `goi_bong_sung` (món mới v1.1). 8 `no_dish` khi hết món làm được. `quan_end` `reason: time` |
| Tiền / uy tín / điểm | 60 + 70 + 90 + 40 = 260, boa 52 → **312**; uy tín 3.0 + 4 × 0.2 = **3.8**; điểm 312 + 100 × 3 = **612**, khớp công thức |

## 2. Smoke `--mode day`

```
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 120000 --snapshot-every 120 \
  --inputs docs/proof/phase-2/day1-inputs.json --out docs/proof/phase-2/day1.jsonl
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 120000 --snapshot-every 120 \
  --inputs docs/proof/phase-2/day5-inputs.json --out docs/proof/phase-2/day5.jsonl
PYTHONPATH=. python3 tools/qa_check_day.py docs/proof/phase-2/day5-inputs.json   # → day5-checks.log
```

| Ngày | Gather (kho bàn giao) | Thu ca | Mua ở Shop | Đầu Ngày kế: `oxygen_max_ticks` / `hp_max` |
|---|---|---|---|---|
| D1 | docked: `ca_loc 3, bong_sung 6` (đúng kế hoạch D1) | 360 | `oxygen` cấp 1 (200) → money 160 | D2: **2700** / 3 |
| D2 | docked: `ca_loc 2, ca_linh 6, bong_dien_dien 2` | 432 | `hp` cấp 1 (250) | D3: 2700 / **4** |
| D3 | docked: `bong_sung 4, ca_loc 2, bong_dien_dien 2, ca_keo 4` (12 ô) | 480 | `oxygen` cấp 2 (400) | D4: **3600** / 4 |
| D4 | docked: 6 loại, gồm `keo_neo` | 432 | `hp` cấp 2 (500) | D5: 3600 / **5** |
| D5 | docked | 456 | (đã tối đa) | n/a |

| AC | Kết quả |
|---|---|
| Thứ tự `day_start → day_plan → phase_start(gather)`; `gather_end`/`quan_end` mang pha cũ, `phase_start` pha mới cùng tick | Đạt |
| `day_plan` D1–D5 khớp bảng ticket (dishes + ingredients) | Đạt |
| Kho mở quán (snapshot `phase_tick 0`) == `gather_end.inventory` **ở cả 5 Ngày** | Đạt ([day5-checks.log](day5-checks.log)) |
| Khách trong `day` chỉ gọi món thuộc `day_plan` | Đạt (23/23 đơn) |
| Shop mở `time_left_ticks 600`, có `stock` dư từ ca | Đạt (D4, D5 dư `ca_keo 1, ca_linh 1`) |
| `bought` trừ `money`, giữ `earned`; cấp hiện ngay ở `upgrades`, `active_upgrades` đổi từ Ngày kế | Đạt |
| Oxy/Máu hồi đầy theo cấp đang hiệu lực, giỏ làm mới đầu Ngày | Đạt (bảng trên; `hold: []` đầu mỗi Ngày) |
| `shop_end(done)`, `days_completed` = 1 / 5, `reason: days_complete` | Đạt |
| Kết thúc 5 Ngày | money 810, earned 2160, reputation 5, score 2660 |
| Hiệu năng: 1 Ngày ≤ 20 s | Đạt: `day --days 1` 0.69 s; `--days 5` 1.10 s; `day` không input (22 200 tick/Ngày) 0.74 s |
| Tất định | Đạt: chạy lại `day1`, `day5`, gather, quan, `cmp` giống từng byte |

## 3. Chưa phủ / ghi nhận

- **Cá Sấu Năm Chèo chưa được hiện thực** ở `4edc10c`: snapshot gather không có `monsters`, chưa có `monster_hit`. Mọi AC mục 1.2 của ticket **chưa kiểm được**.
- Bot không thử `pause` hay `buy_failed`. Hai AC này đang có unit test (`test_pause_freezes_timers_and_resume_runs_same_step`, `test_shop_buy_failures_and_auto_close_after_max_ticks`).
- Ghi nhận nhỏ: khi uy tín chạm trần, JSON in `"reputation":5` (kiểu int, do `reputation_max: 5` trong contract) thay vì `5.0`. Giá trị số vẫn đúng. Nếu máy chấm so byte với bản tham chiếu thì có thể lệch; cần báo lát `quan` (`danhhieu204ns`, `ngominhcuong`).
