# Ma trận kiểm chứng Phase 2 — P2-02 (lunaHieu)

Lượt chạy PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` — **80/80 test đạt, mã thoát Python 0**. Output stdout/stderr thực tế: [monster-survival-test.txt](../proof/phase-2/monster-survival-test.txt).

| Acceptance Criteria | Kiểm chứng | Kết quả / bằng chứng |
|---|---|---|
| AC-P2-M2-01 — Spawn & Ngày | `test_spawn_days_override_and_snapshot_order`, `test_scenario_validation_bad_monsters_exit_2_before_output`: M1 Ngày 1, M1+M2 Ngày 3, scenario thay thế mặc định và dữ liệu sai trả mã 2 trước output. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-02 — Patrol & Chase | `test_patrol_reaches_waypoint_then_targets_other_on_next_step`, `test_chase_detection_and_exit_thresholds`: tốc độ, đổi waypoint, ngưỡng phát hiện/thoát đuổi. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-03 — Hit, LIFO & bất tử | `test_hit_nearest_numeric_id_lifo_and_one_per_tick`, `test_hit_at_post_move_radius_edge_and_depth_gate`, `test_monster_hit_reports_player_position_after_movement`, `test_invulnerability_ends_at_t_plus_90`: một hit, HP, giỏ, vị trí sau bơi, ngưỡng và cooldown. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-04 — Recoil | `test_recoil_60_steps_coincident_direction_and_boundary`, `test_recoil_finishing_tick_cannot_hit`: bắt đầu từ bước sau, lùi 60 tick, kẹp biên và không hit ở tick vừa hết recoil. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-05 — Choke & faint | `test_choke_before_monster_hit_and_choke_ignores_invuln`, `test_monster_faint_loses_remaining_hold_and_inventory_empty`, hồi quy `test_invuln_khong_chan_ngat_theo_contract_v11`: thứ tự event, mất hàng LIFO và kho rỗng. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-06 — Snapshot & nâng cấp | `test_spawn_days_override_and_snapshot_order`, `test_active_upgrade_limits_and_day_spawn`: `monsters[]` sắp ID, `player.invuln_ticks`, trần oxy/HP theo `active_upgrades`. | Phần P2-02 đạt — [output test](../proof/phase-2/monster-survival-test.txt). Snapshot toàn bộ vòng ngày chưa kiểm chứng, chờ P2-03 tích hợp. |

## Lý do cập nhật test Phase 1

Test Contract v1.1 mục 1.1 quy định: **“Ngạt xuyên bất tử và không làm rơi hàng”**. Nghĩa là `choke` không làm rơi nửa giỏ như `monster_hit`; nếu ngạt gây ngất thì `faint` làm mất toàn bộ phần giỏ còn lại. Vì vậy `tests/test_gather_sinh_ton.py` đổi test `test_invuln_chan_ngat` thành `test_invuln_khong_chan_ngat_theo_contract_v11`: với `invuln_ticks=1000`, sau 62 tick hết oxy phải có một `choke` và HP từ 3 xuống 2. Kỳ vọng cũ (HP vẫn 3, không có `choke`) trái với luật v1.1. Chỉ kỳ vọng bị thay đổi; test vẫn chạy headless thật.

`game.contract.json` hiện vẫn ghi v1.0; P2-02 dùng preset v1.1 khi manifest chưa có cấu hình quái/Shop. Người 1 và Người 3 cần tích hợp manifest và vòng ngày; sau khi ghép phải chạy lại toàn suite.
