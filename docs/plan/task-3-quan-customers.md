# DEV 3: GAMEPLAY THỰC KHÁCH & QUẢN LÝ BÀN ĂN (`sim/quan`)

> **File code phụ trách:** `chonoi/sim/quan.py`  
> **Nhiệm vụ:** Xây dựng cỗ máy trạng thái đón khách ghé ghe, xếp bàn ăn, quản lý thanh kiên nhẫn và xử lý khi khách giận dỗi bỏ về.

---

## 1. YÊU CẦU TÍNH NĂNG GAMEPLAY CẦN CODE
1. **Lịch Khách Ghé Quán Nổi:**
   - Bắt đầu từ tick `self.t["first_customer_tick"]`, sau mỗi `int(round(self.t["customer_interval_s"] * TICK))` tick thì có 1 khách mới chèo ghe đến quán.
2. **Xếp Bàn Ăn Trống:**
   - Quét tìm bàn trống đầu tiên trong `self.tables` (`tb.get("customer_id") is None`).
   - Nếu không còn bàn trống: Khách không thể vào quán, bỏ qua chu kỳ này.
   - Nếu có bàn trống: Khách được xếp vào bàn, gán `tb["customer_id"] = customer_id`.
3. **Thanh Kiên Nhẫn (Patience Countdown):**
   - Khởi tạo thời gian kiên nhẫn: `patience_ticks = int(round(self.t["patience_s"] * TICK))`.
   - Mỗi tick, khách đang chờ món (`state == "waiting"`) giảm 1 tick kiên nhẫn.
4. **Khách Giận Dỗi Bỏ Về (Customer Left):**
   - Khi `patience_ticks <= 0`:
     + Khách tức giận rời quán! Phát sự kiện `customer_left`, `data: {"customer_id": c["id"], "table_id": c["table_id"]}`.
     + Giải phóng nguyên liệu đã bị giữ chỗ trong kho (`c["reserved"] = {}`).
     + Phạt trừ uy tín quán: `self.reputation = max(self.t["reputation_min"], round(self.reputation + self.t["left_reputation_delta"], 3))`.
     + Giải phóng bàn (`tb["customer_id"] = None`) và xóa khách khỏi danh sách `self.customers`.

---

## 2. LỆNH CHẠY TEST
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_fixture_khong_hop_le_exit_2 -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_fixture_khong_hop_le_exit_2 -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên Gameplay chuyên sâu về hệ thống Khách hàng ("customer-lifecycle-specialist") phụ trách module `chonoi/sim/quan.py`.

NHIỆM VỤ:
Hoàn thiện logic đón khách, xếp bàn và đếm ngược kiên nhẫn trong class `QuanSim`:
1. Sinh khách theo lịch:
   - Trong `step(inp)`: xác định tick hiện tại. Nếu tick chạm `self.t["first_customer_tick"]` hoặc sau mỗi `int(round(self.t["customer_interval_s"] * TICK))`:
     * Tìm bàn trống đầu tiên trong `self.tables` (bàn có `customer_id is None`). Nếu hết bàn, bỏ qua.
     * Khi có bàn trống và món được chọn (hợp tác với module menu): tạo ID mới `cid = self.ids.new("C")`, thêm khách vào `self.customers` với `{"id": cid, "table_id": tb["id"], "dish": chosen_dish, "state": "waiting", "patience_ticks": int(round(self.t["patience_s"] * TICK)), "reserved": reserved_items}`.
     * Cập nhật `tb["customer_id"] = cid`.
     * Thêm event ("customer_arrived", {"customer_id": cid, "table_id": tb["id"], "dish": chosen_dish}).
2. Quản lý độ kiên nhẫn:
   - Duyệt khách đang `waiting`: giảm `patience_ticks -= 1`.
   - Nếu `patience_ticks <= 0`:
     * Thêm event ("customer_left", {"customer_id": c["id"], "table_id": c["table_id"]}).
     * Hoàn trả nguyên liệu giữ chỗ về kho tự do.
     * Trừ uy tín: `self.reputation = max(self.t["reputation_min"], round(self.reputation + self.t["left_reputation_delta"], 3))`.
     * Đặt lại bàn `tb["customer_id"] = None`, xóa khách khỏi `self.customers`.
Đảm bảo mảng khách được sắp xếp theo ID khi xuất snapshot. Chạy test kiểm tra sau khi code.
```
