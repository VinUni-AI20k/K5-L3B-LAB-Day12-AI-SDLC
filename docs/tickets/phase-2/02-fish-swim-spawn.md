# 02: Cá bơi + sinh + 3 loài + số chuẩn

**What to build:** Đàn cá sống thật: bơi theo dải độ sâu của loài, đổi hướng theo nhịp, nảy ở mép, và sinh thêm theo thời gian tới trần. Buổi sáng thành đi săn thay vì bơi ngắm cảnh.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Đầu ca 8 đàn ở 8 điểm khác nhau lấy từ `fish_spawn_x` × `fish_spawn_depths` theo loài; trần 12.
- [ ] Bơi `fish_speed` (1.5 m/s) trong `fish_x` = [4,96]; cá linh ở d ∈ [3,12], cá lóc [8,20], cá kèo [22,28]; chặn theo dải của loài.
- [ ] Tới mép: phản xạ phần quãng đường còn lại và đảo thành phần hướng vuông góc với mép; chạm góc đảo cả hai.
- [ ] Đổi hướng theo seed ở `phase_tick` bội số `fish_turn_ticks` (120) **trước** khi di chuyển bước đó.
- [ ] Tại `phase_tick = 360·k` (k ≥ 1), **sau** bước bơi: sinh tối đa 1 đàn nếu < 12 và có điểm cách mọi đàn đang sống > `fish_spawn_clearance` (1 m); hết điểm thì bỏ lượt.
- [ ] Loài chọn theo trọng số 40/30/30 **chuẩn hóa lại theo loài còn điểm hợp lệ**, rồi chọn đều một điểm của loài; hướng ban đầu theo seed; phát `fish_spawned {id, kind, pos}`; cá mới tham gia từ bước sau.
- [ ] `random_fish: false` tắt cá mặc định + tắt bơi/sinh; cá fixture (`fish[]`) đứng yên nhưng `age_ticks` vẫn tăng.
- [ ] Bắt cá: chọn đàn gần nhất trong `catch_radius`, hòa theo id, cần đủ chỗ cho **cả** `yield`; xóa đàn; hồi chiêu 30 tick từ lần thành công.
- [ ] Cùng seed + inputs → JSONL giống từng byte, kể cả chuỗi sinh cá.
