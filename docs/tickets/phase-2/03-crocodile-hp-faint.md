# 03: Cá Sấu + Máu/ngất + bất tử

**What to build:** Hai con Cá Sấu tuần tra ở tầng sâu, đuổi khi người chơi lặn xuống gần, cắn mất Máu và làm rơi nửa giỏ. Buổi sáng có nguy hiểm thật, và ngất vẫn mở được quán tối với kho rỗng.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] M1 tuần tra [60,24] ↔ [64,24] từ Ngày 1; M2 từ Ngày 3, [85,18] ↔ [89,18]; waypoint đầu là vị trí xuất phát; `gather` độc lập dùng bố trí Ngày 1.
- [ ] Patrol 1.0 m/s tới waypoint, tới nơi thì đổi mục tiêu **cho bước sau**.
- [ ] Chase 3.0 m/s khi người chơi ở d ≥ 10 và cách ≤ 10 m; về patrol khi cách > 16 m hoặc người chơi lên d < 10; chặn theo biên map và dải sâu của loài.
- [ ] Sau khi **cả hai** di chuyển: nếu cách ≤ 1.5 m, người chơi d ≥ 10 và không bất tử → mất 1 Máu, bỏ `floor(giỏ/2)` nguyên liệu **theo LIFO**, đặt bất tử 90 tick; tối đa một hit mỗi bước, chọn con gần nhất, hòa theo id.
- [ ] Phát `monster_hit {monster_id, hp, lost, pos}` (`lost` là mảng kind theo thứ tự bỏ); trong bất tử không phát hit, không chuyển recoil.
- [ ] Con gây hit vào recoil 60 bước **từ bước sau**, lùi theo hướng xa người chơi đã chốt lúc chạm (trùng tâm dùng +x), mỗi bước 2/60 m trước chặn mép, không gây hit; hết recoil về patrol và xét phát hiện từ bước kế.
- [ ] Máu về 0 → `faint {cause:"monster", lost, hp:0}` rồi `gather_end` `fainted` ngay, bỏ các bước còn lại; quán tối mở với kho rỗng.
- [ ] Thứ tự trong bước: đồng hồ → bơi/oxy/ngạt → quái (cập nhật rồi xét hit) → interact (bến trước hái) → catch (vị trí cá **trước** khi bơi) → hết giờ → cá bơi/sinh.
