# DEV 1: GAMEPLAY LẶN & SINH TỒN ÚT SEN (`sim/gather`)

> **File code phụ trách:** `chonoi/sim/gather.py`  
> **Nhiệm vụ:** Xây dựng cơ chế vật lý lặn ngụp, quản lý dưỡng khí oxy, cơ chế ngạt nước mất máu và cập bến ghe thuyền.

---

## 1. YÊU CẦU TÍNH NĂNG GAME CẦN CODE
1. **Trạng thái Ngoi / Lặn:**
   - So sánh vị trí trước và sau khi di chuyển:
     + Nếu từ dưới nước ($d > \text{surface\_depth}$) ngoi lên mặt nước ($d \le \text{surface\_depth}$): phát sự kiện `surface`, `data: {"pos": list(self.pos)}`.
     + Nếu từ mặt nước chìm xuống nước: phát sự kiện `dive`, `data: {"pos": list(self.pos)}`.
2. **Cơ chế Tiêu hao & Hồi phục Oxy:**
   - Dưới nước: Mỗi tick trừ 1 tick oxy (`self.oxygen_ticks -= 1`).
   - Mặt nước: Mỗi tick hồi `self.t["oxygen_refill_per_tick"]` oxy, kẹp tối đa `self.oxygen_max`.
   - Nếu oxy vừa chạm 0 từ số dương: phát sự kiện `oxygen_empty`.
3. **Cơ chế Ngạt nước (Choke) & Mất Máu:**
   - Khi oxy $= 0$ mà vẫn ở dưới nước: Tăng `self.zero_oxy_ticks += 1`.
   - Khi `self.zero_oxy_ticks >= self.t["choke_interval_ticks"]` (đủ 60 ticks = 1 giây): Reset `self.zero_oxy_ticks = 0`, trừ 1 HP (`self.hp -= 1`), phát sự kiện `choke`, `data: {"hp": self.hp}`.
   - Nếu ở mặt nước: Reset `self.zero_oxy_ticks = 0`.
4. **Ngất xỉu (Faint) & Mất đồ:**
   - Nếu `self.hp <= 0`: Nhân vật ngất xỉu. Xóa sạch giỏ đồ (`self.hold = []`), gọi kết thúc `self._finish("fainted", events)` và return events ngay lập tức.
5. **Cập bến ghe thuyền:**
   - Khi bấm phím `interact` trong bán kính bến (`self._in_dock()`): Kết thúc ca lặn `self._finish("docked", events)`.

---

## 2. LỆNH CHẠY TEST THỬ NGHIỆM
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.Movement -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Movement -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên gameplay phụ trách phát triển cơ chế "Lặn & Sinh Tồn Út Sen" trong file `chonoi/sim/gather.py`.

Hãy triển khai logic sau vào phương thức `step(inp)` của class `GatherSim`:
1. Quản lý trạng thái Dive / Surface:
   - Lưu `was_surface = self._at_surface()` trước khi di chuyển.
   - Sau khi gọi `self._move(inp)`: kiểm tra `is_surface = self._at_surface()`.
   - Nếu `was_surface and not is_surface`: thêm event ("dive", {"pos": list(self.pos)}).
   - Nếu `not was_surface and is_surface`: thêm event ("surface", {"pos": list(self.pos)}).
2. Quản lý Oxy:
   - Nếu `is_surface`: `self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])`, đặt `self.zero_oxy_ticks = 0`.
   - Nếu `not is_surface`:
     * Nếu `self.oxygen_ticks > 0`: `self.oxygen_ticks -= 1`, nếu vừa chạm 0 thì thêm event ("oxygen_empty", {}).
     * Nếu `self.oxygen_ticks == 0`: `self.zero_oxy_ticks += 1`. Khi `self.zero_oxy_ticks >= self.t["choke_interval_ticks"]`: `self.zero_oxy_ticks = 0`, `self.hp -= 1`, thêm event ("choke", {"hp": self.hp}).
     * Nếu `self.hp <= 0`: `self.hold = []`, gọi `self._finish("fainted", events)` và return events.
3. Cập bến:
   - Giữ nguyên kiểm tra `if inp.pressed("interact") and self._in_dock(): self._finish("docked", events); return events`.

Hãy viết code ngắn gọn, chuẩn xác, không dùng thư viện ngoài, đảm bảo không làm gãy các biến snapshot. Chạy test kiểm tra sau khi code xong.
```
