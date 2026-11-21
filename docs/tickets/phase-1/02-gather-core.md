# 02: Gather core — oxy, ngạt, ngất, giỏ

**What to build:** Út Sen lặn xuống thì mất oxy, nổi lên thì hồi; ở dưới nước quá lâu thì bắt đầu mất Máu, hết Máu thì ngất và mất sạch giỏ. Người chơi tự quyết định khi nào nổi lên, và mất mát là thật.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Ở mặt nước (`d <= surface_depth`) 1800 tick: oxy không giảm, hồi `oxygen_refill_per_tick`, kẹp trần.
- [ ] Dưới nước: mỗi tick −1, kẹp 0; chạm 0 phát `oxygen_empty` với `oxygen_ticks: 0`.
- [ ] Bộ đếm ngạt tăng **cả** tick oxy chạm 0 ⇒ lần `choke` đầu ở `t+59`; đủ `choke_interval_ticks` thì đặt lại 0, `hp -= 1`, phát `choke` kèm `hp` sau trừ.
- [ ] Nổi lên đúng bước đáng lẽ bị ngạt thì hồi oxy và **không** ngạt.
- [ ] `hp` về 0: bỏ giỏ theo LIFO, phát `faint` (`cause:"choke"`, `lost` là mảng kind theo thứ tự bỏ, `hp:0`) rồi `gather_end` lý do `fainted` với kho rỗng; dừng bước ngay (không hái/bắt cùng tick).
- [ ] `dive`/`surface` chỉ phát khi đổi phía biên mặt nước, `pos` là vị trí sau khi bơi.
- [ ] Hết giờ: `gather_end` lý do `time` ở mọi độ sâu, giỏ giữ nguyên.
