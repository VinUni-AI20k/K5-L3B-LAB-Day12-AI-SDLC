# 07: Mở rộng — Dòng nước lũ (`current`)

**What to build:** Cứ 30 giây nước lũ ập tới 8 giây, đẩy Út Sen theo một chiều. Báo trước 2 giây để người chơi kịp phản ứng.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Manifest `gather.current {interval_ticks, duration_ticks, warning_ticks, min_depth, speed}`; `extensions` có `current`.
- [ ] Lịch: `t = 1800·k` (k ≥ 1); báo trước ở `t−120` bằng `current_warning {starts_at_phase_tick}`; bắt đầu **trước** di chuyển ở `t`, kéo dài 480 tick.
- [ ] Hướng chọn đều +x/−x theo seed khi bắt đầu; cộng 1.5 m/s vào người chơi nếu `d` đầu bước ≥ 10, rồi chặn mép; **không** tích lũy vào `player.vel`.
- [ ] Kết thúc: `current_end {direction, reason:"elapsed"}` trước di chuyển ở `t+480`; nếu ca kết thúc trước → `current_end(phase_end)` trước `faint`/`gather_end`.
- [ ] Snapshot `current: null` hoặc `{direction, ticks_left}`, đếm cả tick vừa chụp.
- [ ] `random_current:false` tắt lịch; `current_direction:-1|1` khóa hướng; cá và quái **không** chịu lực dòng.
- [ ] Không bật extension → hành vi y như lõi, cùng seed cho cùng byte.
