# Data model — Phase 2 (bổ sung cho `specs/001-phase-1-core/data-model.md`)

## Bộ đếm
| Trường | Ý nghĩa |
|---|---|
| `tick` | bước ngoài, tăng cả khi pause |
| `sim_tick` | bước gameplay (không tính pause) |
| `phase_tick` | bước trong pha hiện tại, `0` ở snapshot đổi pha |

## DayState (`--mode day`)
`day` (1–5), `days_completed`, `money`, `earned` (0 ≤ money ≤ earned), `reputation` [0,5], `upgrades {oxygen:lv, hp:lv}` (đã mua), `active_upgrades` (áp dụng, chép từ `upgrades` khi dựng Ngày mới), `day_plan` (mục của Ngày), `phase ∈ {gather, quan, shop}`, `paused: bool`.
Chuyển: `gather --gather_end--> quan --quan_end--> shop --shop_end--> (days_completed+1) --> gather(day+1) | kết thúc`.

## FishSchool
`id, kind ∈ {ca_linh, ca_loc, ca_keo}, pos [x,d], heading_deg, age_ticks`. Bơi `fish_speed`, miền x `fish_x` [4,96], d theo `fish_depths[kind]`; đổi hướng khi `age_ticks % fish_turn_ticks == 0` (age > 0) trước khi bơi. Sinh: `fish_spawn_ticks` (360), `fish_max` (12), `fish_spawn_clearance` (1), điểm `fish_spawn_x × fish_spawn_depths[kind]`, trọng số `fish_weights`.

## Monster
`id, kind (ca_sau), pos, waypoints [[x,d],[x,d]], target_idx ∈ {0,1}, state ∈ {patrol, chase, recoil}, state_ticks_left, recoil_dir [ux,ud] | null`. Loài: `patrol_speed 1.0, chase_speed 3.0, detect_radius 10, exit_radius 16, depths [10,30], hit_radius 1.5, recoil_ticks 60, recoil_dist 2`. Toàn cục: `invuln_ticks 90, loss_ratio 0.5`. `spawns[].from_day`.

## Player (gather, thêm)
`invuln_ticks` (90 sau hit), `oxygen_max` và `hp_max` theo `active_upgrades` (oxy 30/45/60 s, Máu 3/4/5).

## Quán (đổi)
Bếp B1, B2; bàn T1–T4; khách `order_tick`; menu 6 món; trong `day` lọc theo `day_plan.dishes`.

## Shop
`time_left_ticks` (600, đứng khi pause), `stock` dư (chỉ hiển thị, bỏ sau Shop), upgrades `oxygen[{level,price,oxygen_max_s}]` = [{1,200,45},{2,400,60}], `hp[{level,price,hp_max}]` = [{1,250,4},{2,500,5}].

## DayPlan (dữ liệu chuẩn)
| Ngày | dishes | ingredients |
|---|---|---|
| 1 | ca_loc_nuong_trui 3, goi_bong_sung 3 | ca_loc 3, bong_sung 6 |
| 2 | ca_loc_nuong_trui 2, lau_ca_linh_dien_dien 2 | ca_loc 2, ca_linh 6, bong_dien_dien 2 |
| 3 | goi_bong_sung 2, canh_chua_ca_loc 2, ca_keo_nuong 2 | bong_sung 4, ca_loc 2, bong_dien_dien 2, ca_keo 4 |
| 4 | lau_mam 1, ca_loc_nuong_trui 2, goi_bong_sung 1 | ca_linh 2, ca_keo 1, keo_neo 1, bong_dien_dien 1, ca_loc 2, bong_sung 2 |
| 5 | lau_mam 1, lau_ca_linh_dien_dien 1, ca_loc_nuong_trui 1 | ca_linh 5, ca_keo 1, keo_neo 1, bong_dien_dien 2, ca_loc 1 |

## Menu chuẩn
| id | công thức | nấu | giá |
|---|---|---|---|
| ca_loc_nuong_trui | ca_loc 1 | 6 s | 60 |
| goi_bong_sung | bong_sung 2 | 4 s | 40 |
| lau_ca_linh_dien_dien | ca_linh 3, bong_dien_dien 1 | 10 s | 120 |
| canh_chua_ca_loc | ca_loc 1, bong_dien_dien 1 | 8 s | 90 |
| ca_keo_nuong | ca_keo 2 | 6 s | 70 |
| lau_mam | ca_linh 2, ca_keo 1, keo_neo 1, bong_dien_dien 1 | 12 s | 200 |
