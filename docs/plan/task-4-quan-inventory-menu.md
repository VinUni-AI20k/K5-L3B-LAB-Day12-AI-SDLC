# DEV 4: GAMEPLAY KHO NGUYÊN LIỆU & MENU KHÓA GIỮ CHỖ (`sim/quan`)

> **File code phụ trách:** `chonoi/sim/quan.py` (và `chonoi/inventory.py`)  
> **Nhiệm vụ:** Xây dựng thuật toán kiểm tra kho thực phẩm khả dụng, đối chiếu công thức menu và cơ chế khóa giữ chỗ (Stock Reservation).

---

## 1. YÊU CẦU TÍNH NĂNG GAMEPLAY CẦN CODE
1. **Tính Toán Kho Khả Dụng (Available Stock):**
   - Kho hiện có: `self.stock` (chứa các loại nguyên liệu: `ca_loc`, `ca_linh`, `bong_sung`, `bong_dien_dien`).
   - Tổng nguyên liệu đang bị giữ chỗ: cộng dồn `reserved` từ tất cả các khách hiện có trong quán.
   - Kho khả dụng: `available_stock = current_stock - total_reserved`.
2. **Đối Chiếu Công Thức Menu & Chọn Món Nấu Được:**
   - Đọc danh mục menu từ `self.menu` (hoặc `tuning["menu"]`):
     * `ca_loc_nuong_trui`: cần 1 `ca_loc`
     * `goi_bong_sung`: cần 2 `bong_sung`
     * `lau_ca_linh_dien_dien`: cần 3 `ca_linh`, 1 `bong_dien_dien`
   - Khách ghé quán sẽ chọn món đầu tiên trong menu mà `available_stock` có đủ nguyên liệu để đáp ứng.
3. **Cơ Chế Khóa Giữ Chỗ (Stock Reservation):**
   - Khi chọn được món cho khách: Ngay lập tức tạm khóa số lượng nguyên liệu đó vào `customer["reserved"]`.
   - Không được trừ trực tiếp khỏi `self.stock` ngay lúc này (để kho vẫn hiển thị đúng số lượng nguyên liệu thực tế đang có trong quán).
4. **Xử Lý Hết Món (No Dish):**
   - Nếu `available_stock` không đủ nguyên liệu để nấu bất kỳ món nào trong menu (hoặc hết bàn):
     + Phát sự kiện `no_dish`, `data: {}`.
     + Khách chèo ghe đi tiếp, không vào quán.
5. **Chuyển Giao & Giải Phóng Kho:**
   - Khi bếp bắt đầu nấu món đó: trừ trực tiếp nguyên liệu khỏi `self.stock` và xóa khỏi `customer["reserved"]`.
   - Nếu khách bỏ về giữa chừng (`customer_left`): xóa `customer["reserved"]`, giải phóng nguyên liệu lại cho kho khả dụng.

---

## 2. LỆNH CHẠY TEST
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên Gameplay chuyên sâu về Quản lý Kho & Kinh Tế Menu ("inventory-and-menu-specialist") phụ trách module `chonoi/sim/quan.py`.

NHIỆM VỤ:
Triển khai thuật toán tính kho khả dụng, chọn món và khóa giữ chỗ nguyên liệu (Reservation System):
1. Hàm tính kho khả dụng:
   - Viết helper `_get_available_stock(self) -> dict`:
     * Bắt đầu với bản sao `avail = dict(self.stock)`.
     * Duyệt qua tất cả `c in self.customers`: với mỗi `(item, qty)` trong `c.get("reserved", {}).items()`, trừ `avail[item] -= qty`.
     * Trả về dict `avail`.
2. Hàm chọn món nấu được:
   - Viết helper `_find_cookable_dish(self, avail_stock) -> tuple[str, dict] | None`:
     * Duyệt qua từng món theo thứ tự trong `self.menu`:
     * Kiểm tra từng nguyên liệu trong `recipe`: nếu `avail_stock.get(ing, 0) < need_qty` thì món này không nấu được.
     * Trả về `(dish_name, recipe)` của món đầu tiên nấu được; nếu không có món nào trả về `None`.
3. Tích hợp vào quy trình đón khách:
   - Khi có khách mới đến: gọi `_find_cookable_dish(self._get_available_stock())`.
   - Nếu trả về món: lưu công thức vào `customer["reserved"] = dict(recipe)`.
   - Nếu trả về `None`: phát event ("no_dish", {}).
4. Khấu trừ kho khi nấu bếp:
   - Khi bếp bắt đầu nấu món cho khách: trừ nguyên liệu khỏi `self.stock`, đồng thời xóa `customer["reserved"] = {}` để tránh bị trừ 2 lần.
Hãy viết code an toàn, không làm crash khi số lượng trong kho bằng 0. Chạy test sau khi code xong.
```
