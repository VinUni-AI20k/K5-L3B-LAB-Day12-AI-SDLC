# Ma trận truy vết Phase 1 (PRD-0 · Test Contract v1.0)

- **QA:** `hungdt31` · **Commit được kiểm:** `9b691bd` (merge PR #4, trạng thái Phase 1 trước khi bump contract v1.1) · Python 3.14.4 / Linux.
- Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → **49/49 OK** ([unittest.log](../proof/phase-1/unittest.log)).
- Tên test trong bảng ghi dạng `file::hàm` dưới `tests/`.

## A. Khung, contract, Test Contract headless

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Khai báo nhóm 6 người khớp `team_size` | `python3 tools/check_team.py`; `test_team_check.py` (4 test) | [TEAM.md](../../TEAM.md) | Đạt (`OK: 6 thành viên`) |
| CON-01: `--ticks 0` vẫn ghi dòng `end` | `test_smoke_p1::test_con_01_ticks_zero_and_end_line` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| CON-02: cùng seed → output giống từng byte | `test_con_02_deterministic_bytes` + chạy lại smoke/e2e 2 lần rồi `cmp` | [smoke-gather.jsonl](../proof/phase-1/smoke-gather.jsonl), [smoke-quan.jsonl](../proof/phase-1/smoke-quan.jsonl) | Đạt (smoke và e2e đều giống từng byte) |
| CON-03: input sai / mode cũ, tương lai / scenario sai miền → mã thoát 2 | `test_con_03_*`, `test_scenario_out_of_domain_exit_2`, `ScenarioModes::*` | unittest.log | Đạt |
| Snapshot gather có đủ trường | `test_gather_snapshot_has_gather_fields` | unittest.log | Đạt |
| Smoke `gather` seed 1, 600 tick | `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out …` | [smoke-gather.jsonl](../proof/phase-1/smoke-gather.jsonl) | Đạt (`reason: tick_limit`) |
| Smoke `quan` seed 1, 600 tick | như trên với `--mode quan` | [smoke-quan.jsonl](../proof/phase-1/smoke-quan.jsonl) | Đạt (`reason: tick_limit`) |
| Input: cạnh lên, kế thừa trường vắng, frame sai → lỗi | `test_python_starter_units::test_input_edges_and_inherit`, `test_bad_frames_raise`, `test_catch_is_a_v10_button_and_attack_is_not` | unittest.log | Đạt |
| Id: sắp theo id, cấp id tiếp sau max | `test_id_sorting`, `test_id_allocator_continues_after_max` | unittest.log | Đạt |

## B. Buổi sáng `gather` (Lát 1 `tranha1764`, Lát 2 `ngthanhtamtb`)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| MOVE-01: tốc độ bơi đủ sau ramp | `test_move_01_swim_speed_after_ramp` | unittest.log | Đạt |
| MOVE-02: heading dương là đi xuống | `test_move_02_heading_positive_is_down` | unittest.log | Đạt |
| MOVE-03: chặn mép, `d` không âm, vận tốc về 0 ở mép | `test_move_03_edge_clamp`, `test_move_mep_vel_ve_0` | unittest.log | Đạt |
| Ramp đảo hướng không vượt trần | `test_move_ramp_doi_huong_trong_tran` | unittest.log | Đạt |
| Oxy: lặn từ mặt nước, đếm tick đầu khi hết oxy | `test_gather_oxygen::test_dive_from_surface_boundary_counts_first_empty_tick` | unittest.log | Đạt |
| Oxy: nổi lên đúng tick ngạt thì nạp lại và xóa bộ đếm | `test_surface_on_choke_tick_refills_and_clears_counter` | unittest.log | Đạt |
| Ngất ưu tiên hơn cập bến/hết giờ, giỏ bị xóa | `test_faint_precedes_docking_and_timeout_and_empties_inventory` | unittest.log | Đạt |
| Không có `invuln` trong fixture v1.0 | `test_invulnerability_is_not_a_v10_fixture_field` | unittest.log | Đạt |
| Hái nút gần nhất, hòa thì theo id, mọc lại sau `regrow_s`, giỏ LIFO | `test_gather_rules::test_harvest_nearest_node_tiebreak_regrow_and_lifo` | unittest.log | Đạt |
| Dưới nước không hái được; cập bến được ưu tiên | `test_harvest_blocked_underwater_and_dock_priority` | unittest.log | Đạt |
| Bắt cá dưới nước, cooldown, giỏ đầy | `test_catch_fish_underwater_cooldown_and_hold_full` | unittest.log | Đạt |
| Hết giờ kết thúc buổi và giữ giỏ | `test_time_ends_gather_and_keeps_hold` | unittest.log | Đạt |
| **E2E** bơi → hái N1, N3, N4 → lặn bắt F1 (ca_linh ×3), F4 (ca_loc ×1) → về bến | headless seed 42 với [e2e-gather-inputs.json](../proof/phase-1/e2e-gather-inputs.json) | [e2e-gather.jsonl](../proof/phase-1/e2e-gather.jsonl) | Đạt (`reason: docked` tick 2085; 3 `gather`, 2 `fish_caught`, 2 `dive`/`surface`, 2 `node_regrown`) |

## C. Nối kho 2 tiến trình (Mục G)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| INV-01: gather ghi kho, quan đọc kho | `test_inv_01_gather_writes_inventory_quan_reads_it` | unittest.log | Đạt |
| INV-01: hết tick trước khi cập bến thì không ghi kho | `test_inv_01_not_written_when_tick_limit_first` | unittest.log | Đạt |
| Kho sai schema, kho xung đột với `scenario.stock`, sai mode → mã 2 | `test_inv_bad_schema_exit_2`, `test_inventory_and_scenario_stock_conflict`, `test_inventory_flags_mode_mismatch_exit_2` | unittest.log | Đạt |
| Smoke ngắn: `dock.json` → `handoff-catch.json` → quan tick 0 | `gather --scenario dock.json --inputs dock-inputs.json --ticks 1 --inventory-out …` rồi `quan --inventory … --ticks 0` | [handoff-catch.json](../proof/phase-1/handoff-catch.json), [handoff-gather.jsonl](../proof/phase-1/handoff-gather.jsonl), [handoff-quan.jsonl](../proof/phase-1/handoff-quan.jsonl) | Đạt (`stock` = `{"bong_sung":2,"ca_loc":1}`) |
| **E2E** kho từ vòng gather thật chuyển sang quan | `gather … --inventory-out e2e-kho.json` → `quan --inventory e2e-kho.json` | [e2e-kho.json](../proof/phase-1/e2e-kho.json) | Đạt (`{"bong_dien_dien":1,"bong_sung":2,"ca_linh":3,"ca_loc":1}` khớp giỏ lúc cập bến) |

## D. Buổi tối `quan` (Lát 3 `danhhieu204ns`, Lát 4 `ngominhcuong`)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Khách đến giữ chỗ nguyên liệu, khách mới chờ từ bước sau | `test_quan_customers::test_arrival_reserves_stock_and_new_customer_waits_from_next_step` | unittest.log | Đạt |
| Khách hết kiên nhẫn rời bàn, nhả đơn | `test_waiting_customer_leaves_and_releases_order` | unittest.log | Đạt |
| Đóng quán không phạt khách đang chờ | `test_closing_does_not_penalize_waiting_customer`, `test_closing_pays_eating_and_leaves_waiting_without_rep_loss` | unittest.log | Đạt |
| Nấu → chín → bưng → phục vụ → trả tiền + boa, uy tín +0.2 | `test_quan_slice4::test_full_cook_pick_serve_pay_with_tip` | unittest.log | Đạt |
| Không boa khi kiên nhẫn dưới ngưỡng | `test_no_tip_when_patience_below_threshold` | unittest.log | Đạt |
| Ưu tiên tương tác không rơi xuống mục kế | `test_interact_priority_does_not_fall_through` | unittest.log | Đạt |
| Phục vụ đúng tick kiên nhẫn = 0 vẫn thành công | `test_serve_at_exact_zero_patience_tick_succeeds` | unittest.log | Đạt |
| Bếp chọn đơn cũ nhất, hòa theo id bàn | `test_cook_picks_oldest_order_then_table_id` | unittest.log | Đạt |
| Khách bỏ đi: dọn tay, giảm uy tín, không hoàn nguyên liệu | `test_patience_leave_cleans_hand_and_reduces_reputation_without_refund` | unittest.log | Đạt |
| `player.vel` hợp lệ trong quan | `test_quan_player_vel_hop_le` | unittest.log | Đạt |
| **E2E** ca quán 180 s với kho thật | headless seed 42 với [e2e-quan-inputs.json](../proof/phase-1/e2e-quan-inputs.json) | [e2e-quan.jsonl](../proof/phase-1/e2e-quan.jsonl) | Đạt: 3 khách → 3 `cook_started`/`dish_ready`/`dish_picked`/`served`/`paid` (72 + 48 + 144 = 264, boa 20%), hết kho thì 6 `no_dish`, `quan_end` `reason: time`, money 264, reputation 3.6, score 564 |

Ghi chú: `score = earned + reputation_multiplier × floor(reputation)` (`chonoi/runner.py:34`) → 264 + 100 × 3 = 564, đúng theo khung.

## E. Cửa sổ chơi & UI (`nguyenquangtiep`)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Server live trả state, nhận input, dừng sạch | `test_live::test_state_input_and_clean_stop`, `test_live_inputs_keep_fast_tap_edge` | unittest.log | Đạt |
| HUD sáng/tối, gợi ý tương tác, `--continue-quan` | Kiểm thủ công theo ghi chép của dev UI | [ui-integration.md](../proof/phase-1/ui-integration.md) | Đạt theo ghi chép dev UI; QA chưa quay ảnh hoặc video độc lập |

## F. Hiệu năng & tất định

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| Headless đủ nhanh cho chấm tự động | `/usr/bin/time` cho e2e 10 800 tick | Đạt (gather 0.34 s, quan 0.14 s) |
| E2E tất định | chạy 2 lần, `cmp` jsonl và file kho | Đạt (giống từng byte) |

## Đánh giá ngắn

- **Đạt:** 49/49 test tự động, smoke 2 mode, nối kho 2 tiến trình (cả ngắn lẫn vòng chơi thật), tất định và hiệu năng tại `9b691bd`.
- **Phát hiện khi kiểm chứng (đã xử lý hoặc chuyển tiếp):**
  1. `.gitignore` chặn `*.jsonl` nên các bằng chứng `smoke-*.jsonl` và `handoff-*.jsonl` trước đây không được commit, khiến link trong bảng bị chết. QA đã `git add -f`.
  2. **Hồi quy trên `main`:** commit `bfe5b89` (bump `game.contract.json` lên v1.1, `fish_initial: 8`) làm `chonoi/sim/gather.py:63` lỗi `TypeError: 'int' object is not iterable`, khiến 14 fail và 2 error ([regression-main-bfe5b89.log](../proof/phase-1/regression-main-bfe5b89.log)). Đây là việc dở dang của Phase 2 (cá sinh ngẫu nhiên). **Đề nghị Integrator gắn tag `phase-1` tại `9b691bd`** (hoặc commit chỉ thêm tài liệu, test xanh), không gắn tại `bfe5b89`. Chủ lát `sim/gather` Phase 2 (`tranha1764`) cần sửa trước khi merge tiếp.
- **Chưa đạt / chưa kiểm:** chưa có ảnh chụp HUD độc lập của QA; chưa kiểm trên Windows (dev UI đã kiểm phần này).
- **Điều cần chỉnh cho phase sau:** CI phải chặn merge khi đỏ (`bfe5b89` vào `main` qua PR #8 dù test đỏ). Mỗi PR đổi contract phải chạy lại toàn bộ test. Thêm smoke e2e cho `--mode day`.
