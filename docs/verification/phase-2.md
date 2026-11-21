# Ma trận truy vết Phase 2 — TICKET-02

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Cá đổi hướng ở 120 tick | `test_fish_changes_heading_on_exact_120th_swim_tick` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim cá Phase 2 |
| Cá phản xạ mép | `test_fish_reflects_at_x_edge_and_stays_inside_bounds` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim cá Phase 2 |
| Sinh cá tick 360 và trọng số | `test_fish_spawns_at_tick_360_with_configured_species_weight` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim sinh cá Phase 2 |
| Cá Sấu tuần tra | `test_crocodile_patrols_between_waypoints` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim quái Phase 2 |
| Cá Sấu đuổi theo | `test_crocodile_chases_player_inside_detection_radius` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim quái Phase 2 |
| Cá Sấu cắn, rơi đồ LIFO | `test_crocodile_hit_loses_one_hp_and_half_hold_in_lifo_order` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim quái Phase 2 |
| Bất tử 90 tick, recoil 60 tick | `test_crocodile_is_invulnerable_90_ticks_then_recoils_60_ticks` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ sim quái Phase 2 |
| Quán 2 bếp, 4 bàn | `test_quan_has_two_stoves_and_four_tables` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — cấu hình v1.1 có B1–B2 và T1–T4 |
| Kế hoạch khách D1–D5 | `test_each_day_plan_has_expected_dishes_and_ingredients`, `test_day_headless_announces_d1_to_d5_plan` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Một test dữ liệu đạt; headless D1–D5 chưa đạt vì CLI chưa có `--days`/mode day |
| Shop oxygen/hp, áp dụng Ngày kế | `test_shop_buys_oxygen_at_price_and_applies_next_day` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ Shop trong mode day |
| Pause dừng timer gameplay | `test_pause_freezes_gameplay_tick_and_timer` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Chưa đạt / chờ pause trong mode day |
| Regression Phase 1 | Chạy toàn bộ `unittest discover -s tests -v` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Ghi số đạt/lỗi thật trong log |
| Determinism | Skill `verify-phase`, chạy headless cùng seed hai lần và so SHA-256 | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Ghi kết quả thật trong log |

## Đánh giá ngắn

- QA đã thêm 12 test biên theo TICKET-02; 2 test dữ liệu tĩnh đạt, 10 test hành vi chưa đạt vì sim/CLI v1.1 chưa tích hợp.
- Regression hiện chạy 69 test tổng cộng (57 test nền Phase 1 và 12 test Phase 2): 32 đạt, 21 thất bại, 16 lỗi. Phần lớn lỗi Phase 1 bắt nguồn từ `gather.fish_initial` đã đổi sang số lượng trong contract nhưng `GatherSim` vẫn xử lý như danh sách.
- Determinism chưa thể xác nhận vì headless dừng với cùng lỗi khởi tạo Gather; chi tiết nằm trong proof log.
- Regression Phase 1 phải được chạy lại sau mỗi lần dev tích hợp; không sửa test để che lỗi contract hoặc luật.
- Khi các test chuyển xanh, cập nhật kết quả trong bảng này và gắn tag `phase-2` trên commit bàn giao.
