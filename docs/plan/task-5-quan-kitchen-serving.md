# DEV 5: GAMEPLAY BẾP NẤU, BƯNG BÊ & KINH TẾ QUÁN (`sim/quan`)

> **File code phụ trách:** `chonoi/sim/quan.py`  
> **Nhiệm vụ:** Xây dựng cơ chế bếp nấu thức ăn, bưng bê đĩa món trên tay, phục vụ bàn khách ăn, tính toán doanh thu, tiền tip và uy tín quán nổi.

---

## 1. YÊU CẦU TÍNH NĂNG GAMEPLAY CẦN CODE
1. **Tiến Trình Bếp Nấu Than Hồng:**
   - Bếp đang nấu (`state == "cooking"`) giảm 1 tick đun nấu mỗi tick: `cook_ticks_left -= 1`.
   - Khi `cook_ticks_left == 0`:
     + Bếp chín thức ăn! Đổi `state = "ready"`.
     + Phát sự kiện `dish_ready`, `data: {"stove_id": stove["id"], "dish": stove["dish"]}`.
2. **Thao Tác Nổi Lửa & Bưng Bê (Player Interact):**
   - Khi Út Sen nhấn `interact` trong bán kính `self.t["interact_radius"]`:
     + **Tại Bếp:**
       * Nếu bếp đang rảnh (`state == "idle"`): Tìm khách đang chờ món (`state == "waiting"`). Chuyển bếp sang `state = "cooking"`, gán `dish = món khách gọi`, `cook_ticks_left = int(round(cook_s * TICK))`. Phát `cook_started`.
       * Nếu bếp đã chín (`state == "ready"`) và tay Út Sen rảnh (`self.hand is None`): Bốc đĩa món lên tay (`self.hand = stove["dish"]`), đặt lại bếp `state = "idle"`, phát `dish_picked`.
     + **Tại Bàn:**
       * Nếu Út Sen đang cầm món trên tay (`self.hand is not None`) và tại bàn có khách gọi đúng món đó:
       * Giao món: Đặt `self.hand = None`, khách chuyển sang ăn (`state = "eating"`), `eat_ticks_left = int(round(self.t["eat_s"] * TICK))`.
       * Phát sự kiện `served`, `data: {"customer_id": c["id"], "table_id": tb["id"], "dish": c["dish"]}`.
3. **Khách Ăn, Trả Tiền, Tiền Boa & Điểm Uy Tín:**
   - Khách đang ăn giảm `eat_ticks_left -= 1`. Khi chạm 0:
     + Thu tiền bán món: `price = self.menu[dish]["price"]`. Cộng vào `self.money += price`, `self.earned += price`, `self.shift_earned += price`.
     + Tính tiền boa (Tip): Nếu tỷ lệ kiên nhẫn còn lại $\ge$ `self.t["tip_min_patience_ratio"]`, cộng thêm tiền tip: `tip = int(round(price * self.t["tip_rate"]))`, `self.money += tip`, `self.earned += tip`, `self.shift_earned += tip`.
     + Cộng uy tín quán: `self.reputation = min(self.t["reputation_max"], round(self.reputation + self.t["tip_reputation"], 3))`.
     + Phát sự kiện `paid`, `data: {"customer_id": c["id"], "money": price, "tip": tip}`.
     + Giải phóng bàn (`tb["customer_id"] = None`) và xóa khách.
4. **Hết Ca Đóng Quán (Shift End):**
   - Khi `self.time_left_ticks <= 0`: Kết ca, đặt `self.done = True`, phát sự kiện `quan_end` chứa tổng tài chính và điểm uy tín tích lũy.

---

## 2. LỆNH CHẠY TEST
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_player_vel_hop_le -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_player_vel_hop_le -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên Gameplay chuyên sâu về Bếp nấu & Kinh tế nhà hàng ("kitchen-and-serving-specialist") phụ trách module `chonoi/sim/quan.py`.

NHIỆM VỤ:
Hoàn thiện logic nấu bếp than, bưng món phục vụ và thanh toán trong class `QuanSim`:
1. Đồng hồ bếp nấu:
   - Trong `step(inp)`: lặp qua `self.stoves`. Nếu `s["state"] == "cooking"`: giảm `cook_ticks_left -= 1`. Khi chạm 0: đặt `s["state"] = "ready"`, thêm event ("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}).
2. Xử lý bấm `interact`:
   - Nếu `inp.pressed("interact")`:
     * Tìm đối tượng gần nhất trong `self.t["interact_radius"]` (ưu tiên Bếp trước Bàn, nếu bằng khoảng cách chọn id nhỏ hơn).
     * Với Bếp:
       + Nếu `s["state"] == "idle"`: tìm khách `c` đang `waiting` mà chưa có bếp nào đang nấu món của họ. Chuyển bếp sang `cooking`, `dish = c["dish"]`, `cook_ticks_left = int(round(self.menu[dish]["cook_s"] * TICK))`. Trừ nguyên liệu từ `self.stock`. Thêm event ("cook_started", {"stove_id": s["id"], "dish": dish}).
       + Nếu `s["state"] == "ready"` và `self.hand is None`: `self.hand = s["dish"]`, `s["state"] = "idle"`, `s["dish"] = None`, thêm event ("dish_picked", {"stove_id": s["id"], "dish": self.hand}).
     * Với Bàn:
       + Nếu có khách `c` tại bàn đang `waiting` và `self.hand == c["dish"]`: `self.hand = None`, `c["state"] = "eating"`, `c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))`, thêm event ("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": c["dish"]}).
3. Khách ăn xong & Tính tiền:
   - Duyệt khách `eating`: giảm `eat_ticks_left -= 1`. Khi chạm 0:
     * `price = self.menu[c["dish"]]["price"]`.
     * Tính tip: `is_fast = (c["patience_ticks"] / (self.t["patience_s"] * TICK)) >= self.t["tip_min_patience_ratio"]`. Nếu fast: `tip = int(round(price * self.t["tip_rate"]))`, `self.reputation = min(self.t["reputation_max"], round(self.reputation + self.t["tip_reputation"], 3))`; ngược lại `tip = 0`.
     * `self.money += price + tip`, `self.earned += price + tip`, `self.shift_earned += price + tip`.
     * Thêm event ("paid", {"customer_id": c["id"], "money": price, "tip": tip}).
     * Xóa khách và đặt lại `tb["customer_id"] = None`.
4. Hết giờ: Khi `self.time_left_ticks <= 0`: thêm event ("quan_end", {"reason": "time", "money": self.money, "earned": self.earned, "shift_earned": self.shift_earned, "reputation": self.reputation}).
Chạy test kiểm tra sau khi hoàn thành.
```
