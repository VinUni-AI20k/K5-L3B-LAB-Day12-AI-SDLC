# Ma trận truy vết Phase 2 (TICKET-02 · Test Contract v1.1)

- **QA:** `hungdt31` · **Commit được kiểm:** `d4ce64e` (`main` `b83d2eb` + sửa payload `monster_hit`) · Python 3.14.4 / Linux.
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → **70/70 OK** ([unittest.log](../proof/phase-2/unittest.log)).
- Smoke và bảng số chi tiết: [docs/proof/phase-2/integration.md](../proof/phase-2/integration.md). Tên test ghi dạng `file::hàm` dưới `tests/`.

## 1. Số liệu chuẩn & contract v1.1

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `contract_version: "1.1"`, đủ khóa mục 4.1 (fish_*, `monsters`, B2, T2–T4, 6 món, `day_plan`, `shop`) | Đối chiếu `game.contract.json` với ticket; `contract.py` validate khi chạy | [game.contract.json](../../game.contract.json) | Đạt |
| 6 nguyên liệu, nút N5/N6 `keo_neo`, yield `ca_keo` = 2 | `test_gather_fish_v11::test_new_ingredients_enter_hold_and_export_inventory`; smoke tích hợp | [integration-kho.json](../proof/phase-2/integration-kho.json) | Đạt |
| CLI `--mode day`, `--days 1..5`; mode lạ → mã 2 | `test_smoke_p1::test_con_03_old_and_future_modes_rejected`, `test_day_shop_pause::test_headless_day_cli_end_to_end` | unittest.log | Đạt |

## 2. Buổi sáng: cá bơi/sinh

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Đầu ca 8 đàn ở 8 điểm khác nhau, theo seed | `test_gather_fish_v11::test_initial_schools_use_unique_points_and_seed` | unittest.log | Đạt |
| Cá bơi 1.5 m/s, phản xạ phần quãng còn lại ở mép | `test_reflects_remaining_distance_in_both_axes` | unittest.log | Đạt |
| Đổi hướng ở bước 120, 240… trước khi di chuyển | `test_turn_happens_before_swimming_on_turn_tick` | unittest.log | Đạt |
| Sinh mỗi 360 tick, trần 12, `fish_spawned {id, kind, pos}` | `test_spawn_schedule_uses_elapsed_phase_ticks_and_respects_cap`; smoke (7 lần sinh / 2692 tick) | [integration-gather.jsonl](../proof/phase-2/integration-gather.jsonl) | Đạt |
| `random_fish:false` → cá fixture đứng yên, không sinh | `test_static_fish_fixture_does_not_swim_or_spawn` | unittest.log | Đạt |
| Bắt cá đang bơi, cần đủ chỗ cho cả đàn | `test_gather_rules::test_catch_fish_underwater_cooldown_and_hold_full`; smoke 4 `fish_caught` | unittest.log, integration-gather.jsonl | Đạt |

## 3. Cá Sấu Năm Chèo, Máu, ngất

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| M1 từ Ngày 1, M2 từ Ngày 3 | `test_gather_monsters::test_spawn_by_day_m1_day1_m2_day3`; smoke day5 | [day5-checks.log](../proof/phase-2/day5-checks.log) | Đạt |
| patrol → chase (d ≥ 10, ≤ 10 m) → về patrol khi người chơi lên d < 10 | `test_patrol_chase_hit_lifo_recoil_and_invuln`, `test_chase_and_stop_when_surfacing` | unittest.log | Đạt |
| Hit: −1 Máu, rơi `floor(n/2)` món theo LIFO, bất tử 90 tick, recoil 60 bước | unit test trên + 4 cú hit thật trong day5 (`qa_check_day.py`) | day5-checks.log | Đạt |
| Trùng tâm thì recoil theo +x | `test_coincident_center_recoils_plus_x` | unittest.log | Đạt |
| Máu = 0 → `faint(cause:"monster")`, mất giỏ, `gather_end(fainted)` | `test_faint_by_monster_clears_hold_and_ends_gather` | unittest.log | Đạt |
| **Payload `monster_hit` = `{monster_id, hp, lost, pos}`** | Assert khóa payload trong `test_patrol_chase_hit_lifo_recoil_and_invuln` | commit `d4ce64e` | **Đạt sau khi sửa** (trước đó thiếu `pos`, thừa `kind`) |
| Máu hồi đầy đầu Ngày theo cấp `hp` | smoke day5: `hp_max` 3 → 4 → 5 | [integration.md](../proof/phase-2/integration.md) | Đạt |

## 4. Buổi tối: 2 bếp, 4 bàn, 6 món

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Quán chạy riêng dùng B1/B2, T1–T4, cả 6 món | `test_quan_phase2::test_standalone_uses_all_contract_stoves_tables_and_menu` | unittest.log | Đạt |
| Trong `day`, lọc menu theo `day_plan` **trước** khi lọc nguyên liệu | `test_day_filters_menu_before_checking_available_ingredients`, `test_day_can_choose_only_planned_dishes_and_uses_multiple_tables`; smoke 23/23 đơn thuộc kế hoạch | day5-checks.log | Đạt |
| Phục vụ món mới, tiền + boa + uy tín đúng | smoke tích hợp: 312 / 3.8 / 612 | [integration-quan.jsonl](../proof/phase-2/integration-quan.jsonl) | Đạt |

## 5. Vòng ngày, Shop, pause

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `day_start → day_plan → phase_start(gather)`; event kết thúc mang pha cũ, `phase_start` pha mới cùng tick | `test_day_cycle_shop_upgrade_applies_next_day_and_discards_leftover`; smoke | [day5.jsonl](../proof/phase-2/day5.jsonl) | Đạt |
| `day_plan` D1–D5 đúng bảng ticket | Đối chiếu 5 event `day_plan` | day5.jsonl | Đạt |
| Quán mở với kho bàn giao (cả 5 Ngày) | `qa_check_day.py`: stock tick 0 == `gather_end.inventory` | day5-checks.log | Đạt |
| Kho dư bị bỏ sau Shop, giỏ làm mới đầu Ngày | unit test trên; smoke (D4, D5 Shop có `stock` dư, Ngày sau `hold: []`) | day5-checks.log | Đạt |
| `bought` trừ `money`, giữ `earned`; cấp hiện ngay, `active_upgrades` từ Ngày kế | unit test trên; smoke 4 lần mua | day5-checks.log | Đạt |
| `buy_failed` (`funds`, `max_level`, `unknown`); Shop tự đóng sau 600 tick | `test_shop_buy_failures_and_auto_close_after_max_ticks` (`funds`, `unknown`, tự đóng); `max_level` thử bằng headless (scenario `day.upgrades.oxygen: 2` → `buy_failed max_level`, `hp` vẫn mua được) | unittest.log | Đạt; `max_level` chưa có unit test |
| `pause`/`resumed`: timer đứng yên, cạnh resume chạy gameplay ngay | `test_pause_freezes_timers_and_resume_runs_same_step`; thử headless trong Shop | unittest.log | Đạt |
| Cấm `quan.stock`/`quan.reputation` trong scenario `day` → mã 2 | `test_day_scenario_forbids_quan_stock_and_reputation` | unittest.log | Đạt |
| Kết thúc `reason: days_complete`, `days_completed` | smoke day1, day5 | [day1.jsonl](../proof/phase-2/day1.jsonl), day5.jsonl | Đạt |

## 6. Hiệu năng, tất định, regression P1

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| Headless 1 Ngày ≤ 20 s | `/usr/bin/time` | Đạt (1 Ngày 0.46 s; 5 Ngày 1.26 s) |
| Tất định | Chạy 2 lần rồi `cmp` gather, quan, day1, day5 | Đạt (giống từng byte) |
| Regression P1 với số chuẩn | 49 test P1 vẫn nằm trong bộ 70/70 | Đạt; 3 file test P1 phải đổi, lý do ở bảng dưới |

**Test P1 đổi vì luật v1.1** (lý do ghi trong comment code; commit `e4fc789` chưa ghi lý do trong message nên QA ghi bổ sung tại đây):

| Test | Thay đổi | Lý do theo ticket |
|---|---|---|
| `test_smoke_p1::test_con_03_old_and_future_modes_rejected` | `day` không còn bị từ chối ở v1.1 | v1.1 mở `--mode day` (mục 4.1) |
| `test_gather_oxygen::test_invulnerability_is_not_a_v10_fixture_field` | v1.1 nhận `invuln_ticks ≥ 0`, chỉ âm mới ra mã 2 | Scenario v1.1 thêm `gather.player.invuln_ticks` (mục 4.3); xem [clarify #1](../clarify.md) |
| `test_gather_rules::test_catch_fish_underwater_cooldown_and_hold_full` + snapshot `fish` | Chỉ thử đàn gần nhất, thiếu chỗ thì `hold_full` và không thử đàn kế; số đàn đầu ca đọc từ `fish_initial` | v1.1: "chọn đàn gần nhất… Cần đủ chỗ cho cả đàn"; `fish_initial` là số 8 |

## 7. UI / HUD

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| Menu chính, DayIntro, EveningIntro, DayResult, Summary, menu Pause, HUD sáng/tối, chữ ≥ 18 px @ 1280×720, ≥ 30 FPS | Kiểm thủ công `python3 -m chonoi.live` | QA chạy giao diện. Việc của `hungdt31` trước khi gắn tag |

## Đánh giá ngắn

- **Đạt:** toàn bộ AC lõi chạy headless (contract, cá, Cá Sấu, quán 6 món, vòng ngày, Shop, pause, hiệu năng, tất định).
- **Đã sửa trong lúc kiểm chứng:** payload `monster_hit` lệch Test Contract (thiếu `pos`, thừa `kind`). Commit `d4ce64e` có test khóa payload.
- **Chưa đạt / chưa kiểm:** HUD và menu chưa được QA kiểm thủ công. Mục mở rộng (nhóm 6 người cần ≥ 2 mục trước cuối lab) chưa làm.
- **Ghi nhận nhỏ:** `"reputation":5` in kiểu int khi chạm trần; `snapshot()` trả tham chiếu tới list sống.
- **Đề nghị tag:** gắn `phase-2` tại commit merge của nhánh này (sau `d4ce64e`). Đồng thời gắn bù `phase-1` tại `9b691bd`, vì hiện remote chưa có tag nào.
- **Cho phase sau:** commit đổi test phải ghi lý do trong message. Chạy `tools/qa_check_day.py` mỗi khi đổi schema kho (v1.2).
