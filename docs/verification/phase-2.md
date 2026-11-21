# Ma trận truy vết Phase 2 — TICKET-02

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Cá đổi hướng ở 120 tick | `test_fish_changes_heading_on_exact_120th_swim_tick` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — vận tốc đổi hướng chính xác tại tick 120 |
| Cá phản xạ mép | `test_fish_reflects_at_x_edge_and_stays_inside_bounds` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — phản xạ tại x in [4, 96] và đảo chiều vx |
| Sinh cá tick 360 và trọng số | `test_fish_spawns_at_tick_360_with_configured_species_weight` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — sinh cá định kỳ 360 tick theo trọng số loài |
| Cá Sấu tuần tra | `test_crocodile_patrols_between_waypoints` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — tuần tra giữa các waypoints với tốc độ 1.0 m/s |
| Cá Sấu đuổi theo | `test_crocodile_chases_player_inside_detection_radius` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — phát hiện trong bán kính 10m và đuổi 2.0 m/s |
| Cá Sấu cắn, rơi đồ LIFO | `test_crocodile_hit_loses_one_hp_and_half_hold_in_lifo_order` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — trừ 1 HP, rơi ceil(len/2) vật phẩm theo LIFO |
| Bất tử 90 tick, recoil 60 tick | `test_crocodile_is_invulnerable_90_ticks_then_recoils_60_ticks` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — 90 tick bất tử cho người chơi, 60 tick recoil cho cá sấu |
| Quán 2 bếp, 4 bàn | `test_quan_has_two_stoves_and_four_tables` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — cấu hình v1.1 có B1–B2 và T1–T4 |
| Kế hoạch khách D1–D5 | `test_each_day_plan_has_expected_dishes_and_ingredients`, `test_day_plan_dishes_and_ingredients_contract_days_1_to_5` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — kế hoạch ngày công bố đúng món và nguyên liệu D1–D5 |
| Shop oxygen/hp, áp dụng Ngày kế | `test_shop_buys_oxygen_at_price_and_applies_next_day` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — mua nâng cấp trong shop trừ tiền, áp dụng cho ngày hôm sau |
| Pause dừng timer gameplay | `test_pause_freezes_gameplay_tick_and_timer` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — pause đóng băng sim_tick, phase_tick và thời gian |
| Regression Phase 1 & 2 | Chạy toàn bộ `unittest discover -s tests -v` | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt 93/93 tests (100% OK) |
| Determinism | Skill `verify-phase`, chạy headless cùng seed hai lần và so SHA-256 | [smoke_test.txt](../proof/phase-2/smoke_test.txt) | Đạt — 100% byte-for-byte identical (Run 1 == Run 2) |

## Đánh giá tổng kết

- Toàn bộ tính năng Phase 2 (TICKET-02: Một ngày ở chợ nổi) đã được tích hợp hoàn chỉnh và đồng bộ.
- Bộ kiểm thử gồm 93 bài kiểm thử (bao gồm Unit test, Smoke test P1, Regression, và 12 QA edge tests v1.1) đều vượt qua 100%.
- Tính tất định (Determinism) được kiểm chứng byte-by-byte SHA-256 khớp tuyệt đối qua skill `verify-phase`.
- Sẵn sàng gắn tag `phase-2` để kết thúc và bàn giao Phase 2.
