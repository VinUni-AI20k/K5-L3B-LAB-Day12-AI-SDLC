# DEV 4: GAMEPLAY QUÁN ĂN: BẾP NẤU, BƯNG BÊ & KINH TẾ (`sim/quan`)

> **File code phụ trách:** `chonoi/sim/quan.py`  
> **Nhiệm vụ:** Xây dựng cơ chế tương tác tại bếp nấu, bưng bê món trên tay, phục vụ bàn khách ăn, tính tiền, tiền boa và uy tín quán.

---

## 1. YÊU CẦU TÍNH NĂNG GAME CẦN CODE
1. **Nổi Lửa Bếp Nấu:**
   - Khi Út Sen tới gần Bếp trong `interact_radius` và nhấn `interact`:
     + Nếu bếp đang rảnh (`state == "idle"`) và có khách đang đợi món:
       * Chuyển bếp sang `state = "cooking"`, gán `dish = món cần nấu`, `cook_ticks_left = int(round(cook_s * TICK))`.
       * Trừ trực tiếp nguyên liệu nấu món đó khỏi kho chính `self.stock`, xóa khỏi phần `reserved` của khách.
       * Phát sự kiện `cook_started`, `data: {"stove_id": stove["id"], "dish": dish}`.
2. **Bếp Chín & Bưng Món Lên Tay:**
   - Bếp đang nấu giảm `cook_ticks_left -= 1`. Khi chạm 0 $\rightarrow$ chuyển `state = "ready"`, phát `dish_ready`.
   - Khi Út Sen nhấn `interact` tại bếp đã chín (`state == "ready"`):
     + Nếu tay đang rảnh (`self.hand is None`): bốc món lên tay `self.hand = stove["dish"]`, đặt lại bếp `state = "idle"`, phát `dish_picked`.
3. **Phục Vụ Bàn & Khách Ăn:**
   - Khi Út Sen cầm món tới gần Bàn có khách gọi đúng món đó, nhấn `interact`:
     + Đặt món xuống bàn: `self.hand = None`, khách chuyển sang `state = "eating"` với `eat_ticks_left = int(round(self.t["eat_s"] * TICK))`.
     + Phát sự kiện `served`, `data: {"customer_id": c["id"], "table_id": tb["id"], "dish": dish}`.
4. **Thanh Toán Tiền, Tiền Boa & Uy Tín:**
   - Khách ăn xong (`eat_ticks_left == 0`):
     + Cộng tiền bán món theo menu: `self.money += price`, `self.earned += price`, `self.shift_earned += price`.
     + Tính tiền boa: Nếu tỷ lệ kiên nhẫn còn lại $\ge$ `self.t["tip_min_patience_ratio"]`, cộng thêm tiền tip `= int(round(price * self.t["tip_rate"]))` và cộng uy tín `self.t["tip_reputation"]`.
     + Phát sự kiện `paid`, khách rời bàn, bàn trở thành trống.
5. **Đóng Ca Hết Giờ:**
   - Khi `self.time_left_ticks <= 0`: đặt `self.done = True`, phát `quan_end` chứa tổng kết tài chính và uy tín.

---

## 2. LỆNH CHẠY TEST THỬ NGHIỆM
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên gameplay phụ trách phát triển hệ thống "Bếp Nấu, Bưng Bê & Kinh Tế Quán" trong file `chonoi/sim/quan.py`.

Hãy triển khai logic tương tác Bếp, Bưng bê, Phục vụ và Thanh toán trong class `QuanSim`:
1. Tiến trình Bếp nấu:
   - Duyệt `self.stoves`: nếu `state == "cooking"`, giảm `cook_ticks_left -= 1`. Khi chạm 0: đặt `state = "ready"`, phát event ("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}).
2. Xử lý phím `interact`:
   - Nếu `inp.pressed("interact")`:
     * Tìm đối tượng gần nhất trong `self.t["interact_radius"]` (ưu tiên Bếp trước Bàn, nếu bằng khoảng cách ưu tiên id nhỏ hơn).
     * Tương tác với Bếp:
       + Nếu bếp `idle`: tìm khách đầu tiên có `state == "waiting"` mà chưa có bếp nào đang nấu món của họ. Chuyển bếp thành `state = "cooking"`, `dish = customer["dish"]`, `cook_ticks_left = int(round(self.menu[dish]["cook_s"] * TICK))`. Trừ nguyên liệu khỏi `self.stock` và xóa khỏi `customer["reserved"]`. Phát event ("cook_started", {"stove_id": s["id"], "dish": dish}).
       + Nếu bếp `ready` và `self.hand is None`: lấy món `self.hand = s["dish"]`, đặt lại `s["state"] = "idle"`, `s["dish"] = None`, phát event ("dish_picked", {"stove_id": s["id"], "dish": self.hand}).
     * Tương tác với Bàn:
       + Nếu có khách tại bàn đang `waiting` và `self.hand == customer["dish"]`: giao món, đặt `self.hand = None`, khách chuyển sang `state = "eating"`, `eat_ticks_left = int(round(self.t["eat_s"] * TICK))`, phát event ("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": customer["dish"]}).
3. Khách ăn & Thanh toán:
   - Khách có `state == "eating"`: giảm `eat_ticks_left -= 1`. Khi chạm 0:
     * Cộng tiền: `price = self.menu[c["dish"]]["price"]`, tính tip nếu `c["patience_ticks"] / (self.t["patience_s"] * TICK) >= self.t["tip_min_patience_ratio"]`.
     * Cộng điểm uy tín `self.reputation = min(self.t["reputation_max"], round(self.reputation + self.t["tip_reputation"], 3))`.
     * Phát event ("paid", {"customer_id": c["id"], "money": price, "tip": tip}), giải phóng bàn và xóa khách.
4. Kết thúc ca: Hết giờ phát `quan_end` chứa `money, earned, shift_earned, reputation`.
Chạy test sau khi code xong.
```
