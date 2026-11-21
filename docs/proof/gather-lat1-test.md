# Kết quả test — lát 1 gather (haidoan2426)

Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (python3 = Python 3.13 qua WindowsApps)

Kết quả: **45 test, 0 lỗi, exit 0**. Chưa commit tại thời điểm chạy.

Test mới: `tests/test_gather_sinh_ton.py` — 9 test sinh tồn (dive, surface, oxy giảm/hồi/kẹp max, oxygen_empty, ngạt, reset bộ đếm ngạt, invuln, ngất) + 4 test giỏ (LIFO trong snapshot, sức chứa 12 chấp nhận / 13 từ chối exit 2, hết giờ ghi kho theo số lượng, ngất làm rỗng giỏ).

Chưa test: nhặt đồ làm giỏ đầy (`hold_full`) và LIFO khi nhặt — thuộc lát 2 (hái/bắt cá) chưa làm.

```
test_gi\u1ecf_day_12_chap_nhan_va_tren_12_tu_choi (test_gather_sinh_ton.Hold.test_gi\u1ecf_day_12_chap_nhan_va_tren_12_tu_choi) ... ok
test_het_gio_ghi_kho_theo_so_luong_trong_gio (test_gather_sinh_ton.Hold.test_het_gio_ghi_kho_theo_so_luong_trong_gio) ... ok
test_ngat_gi\u1ecf_day_mat_het (test_gather_sinh_ton.Hold.test_ngat_gi\u1ecf_day_mat_het) ... ok
test_snapshot_giu_thu_tu_nhat_lifo (test_gather_sinh_ton.Hold.test_snapshot_giu_thu_tu_nhat_lifo) ... ok
test_dive_khi_roi_mat_nuoc (test_gather_sinh_ton.Survival.test_dive_khi_roi_mat_nuoc) ... ok
test_hoi_oxy_reset_bo_dem_ngat (test_gather_sinh_ton.Survival.test_hoi_oxy_reset_bo_dem_ngat) ... ok
test_invuln_chan_ngat (test_gather_sinh_ton.Survival.test_invuln_chan_ngat) ... ok
test_mau_ve_0_ngat_xiu_mat_gio (test_gather_sinh_ton.Survival.test_mau_ve_0_ngat_xiu_mat_gio) ... ok
test_ngat_mat_1_mau_dung_choke_interval (test_gather_sinh_ton.Survival.test_ngat_mat_1_mau_dung_choke_interval) ... ok
test_oxy_giam_moi_tick_duoi_nuoc (test_gather_sinh_ton.Survival.test_oxy_giam_moi_tick_duoi_nuoc) ... ok
test_oxy_hoi_moi_tick_o_mat_nuoc_va_kep_max (test_gather_sinh_ton.Survival.test_oxy_hoi_moi_tick_o_mat_nuoc_va_kep_max) ... ok
test_oxygen_empty_dung_dung_mot_lan (test_gather_sinh_ton.Survival.test_oxygen_empty_dung_dung_mot_lan) ... ok
test_surface_khi_noi_len (test_gather_sinh_ton.Survival.test_surface_khi_noi_len) ... ok
test_state_input_and_clean_stop (test_live.LiveServerTest.test_state_input_and_clean_stop) ... ok
test_bad_frames_raise (test_python_starter_units.Units.test_bad_frames_raise) ... ok
test_catch_is_a_v10_button_and_attack_is_not (test_python_starter_units.Units.test_catch_is_a_v10_button_and_attack_is_not) ... ok
test_id_allocator_continues_after_max (test_python_starter_units.Units.test_id_allocator_continues_after_max) ... ok
test_id_sorting (test_python_starter_units.Units.test_id_sorting) ... ok
test_input_edges_and_inherit (test_python_starter_units.Units.test_input_edges_and_inherit) ... ok
test_live_inputs_keep_fast_tap_edge (test_python_starter_units.Units.test_live_inputs_keep_fast_tap_edge) ... ok
test_session_steps_gather_and_dock (test_python_starter_units.Units.test_session_steps_gather_and_dock) ... ok
test_con_01_ticks_zero_and_end_line (test_smoke_p1.Contract.test_con_01_ticks_zero_and_end_line) ... ok
test_con_02_deterministic_bytes (test_smoke_p1.Contract.test_con_02_deterministic_bytes) ... ok
test_con_03_bad_input_exit_2 (test_smoke_p1.Contract.test_con_03_bad_input_exit_2) ... ok
test_con_03_old_and_future_modes_rejected (test_smoke_p1.Contract.test_con_03_old_and_future_modes_rejected) ... ok
test_gather_snapshot_has_gather_fields (test_smoke_p1.Contract.test_gather_snapshot_has_gather_fields) ... ok
test_scenario_out_of_domain_exit_2 (test_smoke_p1.Contract.test_scenario_out_of_domain_exit_2) ... ok
V� d\u1ee5 smoke test trong PRD-0 m\u1ee5c G: c\u1eadp b\u1ebfn \u1edf tick 0, qu�n �\u1ecdc kho ��ng n\u1ed9i dung. ... ok
test_inv_01_not_written_when_tick_limit_first (test_smoke_p1.Integration.test_inv_01_not_written_when_tick_limit_first) ... ok
test_inv_bad_schema_exit_2 (test_smoke_p1.Integration.test_inv_bad_schema_exit_2) ... ok
test_inventory_and_scenario_stock_conflict (test_smoke_p1.Integration.test_inventory_and_scenario_stock_conflict) ... ok
test_inventory_flags_mode_mismatch_exit_2 (test_smoke_p1.Integration.test_inventory_flags_mode_mismatch_exit_2) ... ok
B\u1ecf 6 tick t�ng t\u1ed1c r\u1ed3i �o 60 tick: qu\xe3ng \u2248 swim_speed � 1 s (�0.1). Ngang, xu\u1ed1ng, ch�o (kh�ng nhanh h�n). ... ok
test_move_02_heading_positive_is_down (test_smoke_p1.Movement.test_move_02_heading_positive_is_down) ... ok
Ch\u1eb7n t\u1eebng m�p c\u1ee7a v�ng n�\u1edbc, k\u1ec3 c\u1ea3 d kh�ng �m (kh�ng bay l�n kh\u1ecfi m\u1eb7t n�\u1edbc) v� ��y d = 30. ... ok
test_move_mep_vel_ve_0 (test_smoke_p1.Movement.test_move_mep_vel_ve_0) ... ok
�\u1ea3o t\u1eeb +speed sang -speed: v\u1eadn t\u1ed1c ch\u1ea1m m\u1ee5c ti�u sau t\u1ed1i �a ramp_max_ticks tick k\u1ec3 t\u1eeb l�c �\u1ed5i input. ... ok
test_time_ends_gather_and_keeps_hold (test_smoke_p1.Movement.test_time_ends_gather_and_keeps_hold) ... ok
test_khoi_sai_mode_exit_2 (test_smoke_p1.ScenarioModes.test_khoi_sai_mode_exit_2) ... ok
test_quan_fixture_khong_hop_le_exit_2 (test_smoke_p1.ScenarioModes.test_quan_fixture_khong_hop_le_exit_2) ... ok
test_quan_player_vel_hop_le (test_smoke_p1.ScenarioModes.test_quan_player_vel_hop_le) ... ok
test_good (test_team_check.TeamCheck.test_good) ... ok
test_template_is_rejected (test_team_check.TeamCheck.test_template_is_rejected) ... ok
test_too_few_members (test_team_check.TeamCheck.test_too_few_members) ... ok
test_wrong_size_duplicate_and_outsider (test_team_check.TeamCheck.test_wrong_size_duplicate_and_outsider) ... ok
Ran 45 tests in 6.693s
OK
```
