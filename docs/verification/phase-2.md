# Ma trận truy vết Phase 2 (contract v1.1)

Cách kiểm chung: `python3 tools/run_checks.py` · test riêng: `PYTHONPATH=tests:. python3 -m unittest discover -s tests`.

## Ticket 01 — prefactor v1.1 (xong)

| AC | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| Manifest 1.1: 8 đàn, 6 món, 3 loài, 6 nút, monsters, day_plan 5 Ngày, shop, extensions | `test_contract_v11.Manifest` | `docs/proof/phase-1/checks-latest.md` | đạt |
| `--mode day --ticks 0` chạy; snapshot có `day, day_plan, upgrades, active_upgrades` | `test_day_ticks_zero_has_day_fields` | nt | đạt |
| `--days` chỉ với `day`, trong [1,5] | `test_days_bounds_and_mode` | nt | đạt |
| `day` cấm `quan.stock` / `quan.reputation` | `test_day_scenario_rejects_stock_and_reputation` | nt | đạt |
| Scenario nhận `monsters[]`, `ca_ho`, `fish[].age_ticks`, `player.invuln_ticks/attack_cd_ticks` | `test_monsters_fixture`, `test_fish_age_ticks`, `test_player_invuln_and_attack_cooldown_accepted` | nt | đạt |
| Không hồi quy P1 | 103 test OK | nt | đạt |

## Test P1 phải sửa — lý do (bắt buộc ghi theo PRD)

| Test | Trước | Sau | Lý do |
|---|---|---|---|
| `test_gather_snapshot_has_gather_fields` | `len(fish) == 6` | `== 8` | Contract v1.1 chuẩn hoá **8 đàn** đầu ca (PRD Phase 2 §1.1) |
| `test_con_03_old_and_future_modes_rejected` | `day` phải bị từ chối | chỉ còn `river` | v1.1 hỗ trợ `--mode day`; danh sách mode cũ vẫn bị từ chối |
| `KINDS_P1` (inventory) | 4 nguyên liệu | 6 (`+ca_keo`, `+keo_neo`) | 2 nguyên liệu mới của thực đơn 6 món |

## Còn lại của Phase 2

Cá bơi/sinh (02), Cá Sấu (03), quán 2 bếp/4 bàn/6 món (04), `day` + Shop + pause (05), HUD (06), mở rộng `net` (07).

## Ticket 03 — Cá Sấu (xong, chờ merge)

| AC | Cách kiểm | Kết quả |
|---|---|---|
| Patrol 1.0 m/s, tới waypoint thì đổi mục tiêu cho bước sau | `test_monsters.Patrol` | đạt |
| Chỉ M1 ở Ngày 1; M2 từ Ngày 3 | `test_chi_co_m1_ngay_1` | đạt |
| Chase 3.0 m/s khi người chơi d ≥ 10 và cách ≤ 10 m; về patrol khi > 16 m hoặc lên mặt nước | `test_monsters.Chase` | đạt |
| Chạm: −1 Máu, rơi `floor(giỏ/2)` theo LIFO, bất tử 90 tick, `monster_hit {monster_id,hp,lost,pos}` | `test_hit_mat_mau_roi_nua_gio_va_bat_tu` | đạt |
| Bất tử không bị hit lần hai | `test_bat_tu_khong_bi_hit_lan_hai` | đạt |
| Recoil 60 bước từ bước sau, lùi xa người chơi, không gây hit | `test_recoil_lui_ra_va_khong_hit` | đạt |
| Không hit khi người chơi ở mặt nước | `test_khong_hit_khi_nguoi_choi_o_mat_nuoc` | đạt |
| Máu 0 do quái: `faint {cause:"monster"}`, `gather_end` fainted, kho rỗng | `test_ngat_do_quai_kho_rong_va_gather_end` | đạt |
| Scenario `monsters[]` thay danh sách mặc định | `test_scenario_thay_danh_sach_quai` | đạt |

## Ticket 04 — Quán Ăn mở rộng (xong)

| AC | Cách kiểm | Kết quả |
|---|---|---|
| Hai bếp B1 [2,8], B2 [5,8] nấu song song độc lập, không giẫm đơn nhau | `test_quan_p2.TestQuanP2.test_two_stoves_cook_parallel_without_collision` | đạt |
| Bốn bàn T1–T4: kín 4 bàn thì hết chỗ (`free_table` trả về None) | `test_quan_p2.TestQuanP2.test_four_tables_capacity` | đạt |
| 6 món với 2 nguyên liệu mới (`ca_keo`, `keo_neo`): nấu món lẩu mắm chốt giá 200đ, items sắp alphabet | `test_quan_p2.TestQuanP2.test_six_dishes_and_new_ingredients` | đạt |
| Trong `day`: lọc menu theo `day_plan.dishes` trước; quán độc lập dùng cả 6 món | `test_quan_p2.TestQuanP2.test_day_plan_filtering` | đạt |
| Kế hoạch ngày không phải trần bán: khách vẫn gọi được tiếp khi còn nguyên liệu | `test_quan_p2.TestQuanP2.test_day_plan_filtering` | đạt |
| Có bàn trống nhưng không món nào đủ nguyên liệu -> phát `no_dish` và không sinh khách | `test_quan_p2.TestQuanP2.test_no_dish_when_ingredients_insufficient` | đạt |
| `random_customers: false` không sinh khách tự động | `test_quan_p2.TestQuanP2.test_random_customers_false` | đạt |
