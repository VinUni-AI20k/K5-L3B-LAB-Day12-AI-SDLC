---
name: gather-sim
description: Chuyên gia mô phỏng chế độ Lặn & Thu hoạch (gather) của Quán Ăn Chợ Nổi
---

# Gather Sim Skill

Dùng khi triển khai hoặc sửa đổi logic lặn, hái bông và bắt cá trong `chonoi/sim/gather.py`.

## Nguyên tắc:
1. Đọc tham số từ `self.t` (đọc từ `game.contract.json["tuning"]["gather"]`), không hard-code số liệu.
2. Oxy tiêu hao 1 tick/tick khi $d > \text{surface\_depth}$; hồi `oxygen_refill_per_tick` khi $d \le \text{surface\_depth}$.
3. Khi oxy chạm 0: đếm `zero_oxy_ticks`, đủ `choke_interval_ticks` thì trừ 1 HP (`choke`).
4. Khi HP về 0: ngất (`fainted`), giỏ rỗng, kết thúc ca.
5. Hái bông và bắt cá theo cơ chế bán kính, giỏ đồ LIFO, kẹp sức chứa `hold_capacity`.
6. Chỉ dùng RNG từ `self.rng` (`Streams`), không dùng random ngoài.
