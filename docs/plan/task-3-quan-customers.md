# DEV 3: GAMEPLAY QUÁN ĂN: THỰC KHÁCH & MENU (`sim/quan`)

> **File code phụ trách:** `chonoi/sim/quan.py`  
> **Nhiệm vụ:** Xây dựng hệ thống đón khách ghé ghe, xếp bàn, chọn món theo kho nguyên liệu, cơ chế giữ chỗ (reserved) và thanh kiên nhẫn.

---

## 1. YÊU CẦU TÍNH NĂNG GAME CẦN CODE
1. **Lịch Khách Đến Ghe:**
   - Bắt đầu từ tick `self.t["first_customer_tick"]`, sau mỗi `int(round(self.t["customer_interval_s"] * TICK))` tick thì đón 1 khách mới.
2. **Tìm Bàn & Chọn Món Nấu Được:**
   - Tìm bàn trống đầu tiên trong `self.tables` (`customer_id is None`). Nếu hết bàn $\rightarrow$ không đón thêm.
   - Tính toán kho khả dụng: `available = kho hiện tại - tổng nguyên liệu khách khác đang giữ chỗ`.
   - Tìm món đầu tiên trong `self.menu` mà kho khả dụng có đủ nguyên liệu để nấu:
     + Nếu tìm thấy: Tạo khách mới với ID cấp từ `self.ids.new("C")`, gán `table_id`, lưu món gọi `dish`, khóa số nguyên liệu cần dùng vào `customer["reserved"]`, khởi tạo `patience_ticks = int(round(self.t["patience_s"] * TICK))`. Phát sự kiện `customer_arrived`.
     + Nếu không có món nào nấu được: Phát sự kiện `no_dish`, `data: {}`.
3. **Thanh Kiên Nhẫn & Khách Bỏ Về:**
   - Mỗi tick, khách đang chờ món (`dish` chưa được phục vụ) giảm 1 tick kiên nhẫn.
   - Khi kiên nhẫn chạm 0:
     + Khách bỏ về! Phát sự kiện `customer_left`, `data: {"customer_id": c["id"], "table_id": c["table_id"]}`.
     + Giải phóng nguyên liệu đã giữ chỗ trong kho (`reserved`).
     + Trừ điểm uy tín quán: `self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])`.
     + Xóa khách khỏi bàn và khỏi danh sách khách.

---

## 2. LỆNH CHẠY TEST THỬ NGHIỆM
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_fixture_khong_hop_le_exit_2 -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.ScenarioModes.test_quan_fixture_khong_hop_le_exit_2 -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên gameplay phụ trách phát triển hệ thống "Thực Khách & Menu Quán Ăn" trong file `chonoi/sim/quan.py`.

Hãy triển khai logic quản lý khách hàng và giữ chỗ nguyên liệu:
1. Đón khách mới theo lịch trình:
   - Trong `step(inp)`: kiểm tra nếu tick hiện tại (tính từ thời gian trôi qua) chạm mốc `self.t["first_customer_tick"]` hoặc lặp lại chu kỳ `int(round(self.t["customer_interval_s"] * TICK))`:
     * Tìm bàn trống (`table["customer_id"] is None`). Nếu không có bàn trống, bỏ qua.
     * Tính kho khả dụng: sao chép `self.stock`, trừ đi số lượng nguyên liệu mà tất cả khách hiện tại đang giữ trong `c["reserved"]`.
     * Duyệt qua từng món trong `self.menu`: kiểm tra xem kho khả dụng có đủ nguyên liệu theo `recipe` của món không.
     * Nếu tìm thấy món: cấp ID `cid = self.ids.new("C")`, tạo khách `{"id": cid, "table_id": tb["id"], "dish": dish_name, "state": "waiting", "patience_ticks": int(round(self.t["patience_s"] * TICK)), "reserved": dict(recipe)}`. Thêm vào `self.customers`, cập nhật bàn `tb["customer_id"] = cid`. Phát event ("customer_arrived", {"customer_id": cid, "table_id": tb["id"], "dish": dish_name}).
     * Nếu không có món nào nấu được: phát event ("no_dish", {}).
2. Đếm ngược kiên nhẫn & khách bỏ về:
   - Duyệt các khách có `state == "waiting"`: giảm `patience_ticks -= 1`.
   - Nếu `patience_ticks <= 0`:
     * Thêm event ("customer_left", {"customer_id": c["id"], "table_id": c["table_id"]}).
     * Cập nhật uy tín: `self.reputation = max(self.t["reputation_min"], round(self.reputation + self.t["left_reputation_delta"], 3))`.
     * Giải phóng bàn `tb["customer_id"] = None`, xóa khách khỏi `self.customers`.
Đảm bảo danh sách khách được sắp xếp đúng ID khi snapshot. Chạy test sau khi code xong.
```
