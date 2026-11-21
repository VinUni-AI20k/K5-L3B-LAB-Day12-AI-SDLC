# Tiêu chí chấp nhận M1 — Phase 1

Theo [PRD-0, mục E–G](../../PRD0.md#L208) và [hợp đồng Phase 1](../contracts/README.md).

| AC | Hành vi cần kiểm chứng | Test |
|---|---|---|
| M1-AC1 | Vận tốc tiến tới đích trong giới hạn ramp. Chặn vị trí tại biên, triệt vận tốc hướng ra ngoài. Hướng mặt theo input di chuyển gần nhất. | `test_smoke_p1.Movement` |
| M1-AC2 | Chỉ phát `dive` / `surface` khi đổi vùng qua ngưỡng mặt nước. Payload là vị trí sau di chuyển. Tính oxy theo vùng cuối tick. | `test_water_crossings_use_position_after_movement` |
| M1-AC3 | Oxy dưới nước giảm 1 mỗi tick, chặn tại 0. Chỉ phát `oxygen_empty` khi từ dương về 0. Tính tick cạn đầu tiên vào thời gian ngạt, trừ đúng 1 Máu và reset bộ đếm mỗi chu kỳ. | `test_choking_counts_first_empty_tick_and_repeats` |
| M1-AC4 | Trên mặt nước hồi oxy đến trần và reset ngạt. Nổi đúng tick đáng lẽ bị ngạt thì không mất Máu. | `test_surfacing_on_choke_tick_resets_counter_and_caps_refill` |
| M1-AC5 | Khi Máu về 0, phát `choke`, `faint` với đồ mất theo LIFO, rồi `gather_end` với lý do `fainted` và kho rỗng. Dừng tick trước tương tác, bắt cá hoặc xét hết giờ. | `test_faint_empties_inventory_before_docking_or_timeout` |
