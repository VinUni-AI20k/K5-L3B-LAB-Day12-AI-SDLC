# 05: `day` + Shop + pause

**What to build:** Chơi trọn một Ngày và trọn 5 Ngày: intro kế hoạch → lặn → quán → kết quả → Shop → Ngày kế. Tiền, uy tín và cấp nâng cấp giữ qua Ngày; pause đóng băng mọi thứ.

**Blocked by:** 01 (mềm: 02–04 — dựng được bằng fixture trước khi các lát xong)

**Status:** ready-for-agent

- [ ] `--mode day --days N` (1..5, mặc định 1) chạy được; bàn giao giữa các pha **trong bộ nhớ**, không ghi file kho.
- [ ] Thứ tự pha `day_start → day_plan → phase_start(gather) → phase_start(quan) → phase_start(shop)`; chuyển pha **cùng tick**, gameplay pha mới từ bước sau; snapshot đổi pha có `phase_tick: 0`, event kết thúc mang pha cũ.
- [ ] `sim_tick` liên tục suốt Ngày; `phase_tick` reset 0 mỗi pha; Ngày không pause tối đa 22.200 tick.
- [ ] Snapshot trong `day` có `day, day_plan, upgrades, active_upgrades` (cấp đã mua vs cấp đang áp dụng); Shop có `stock` dư và `time_left_ticks`.
- [ ] Pause: xét cạnh `pause` trước mọi thứ; khi paused chỉ `tick` ngoài tăng, `sim_tick/phase_tick/timer` đứng yên, phát `paused`; cạnh kế tiếp phát `resumed` và chạy gameplay ngay bước đó.
- [ ] Shop nhận `buy` (chuỗi) mỗi lệnh một đơn vị: `oxygen` 200→45 s / 400→60 s, `hp` 250→4 Máu / 500→5 Máu; mua cấp kế tiếp một lần; đủ đúng giá vẫn mua được; phát `bought` hoặc `buy_failed {action, reason}` với `funds/max_level/out_of_stock/unknown`.
- [ ] Xử lý `buy` **trước** cạnh `shop_done` kể cả bước cuối; Shop tự đóng sau 600 tick hoạt động; phát `shop_end {reason}`; đóng Shop thì tăng `days_completed` và dựng Ngày kế **ngay tick đó**, chỉ lúc đó mới sao cấp đã mua sang `active_upgrades`.
- [ ] Sang Ngày mới: oxy/Máu hồi đầy theo cấp có hiệu lực, giỏ làm mới, kho dư bị bỏ; tiền/earned/uy tín giữ nguyên.
- [ ] Dòng `end` có `days_completed`; đủ 5 Ngày → `reason:"days_complete"`.
- [ ] `day` tất định: cùng seed/inputs → cùng byte; một Ngày ≤ 22.200 tick chạy ≤ 20 s.
