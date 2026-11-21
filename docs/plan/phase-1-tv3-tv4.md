# Phối hợp TV3 và TV4 trong Phase 1

Đề xuất để TV3 và TV4 xác nhận trước khi sửa `chonoi/sim/quan.py`.

## Dữ liệu dùng chung

Starter lưu khách trong `self.customers` và nguyên liệu giữ chỗ trong `customer["reserved"]`. Hai phần dùng chung `order_id`, `order_tick`, mã món, trạng thái đơn và `patience_ticks_left`. Khi xác nhận giao diện, đối chiếu tên trường và giá trị trạng thái với mục F phần Quán của Test Contract.

## Giữ, trừ và nhả nguyên liệu

- Khi khách gọi, TV3 ghi số lượng cần vào `reserved` của khách. Kho khả dụng bằng `self.stock` trừ tổng lượng đang giữ cho các đơn.
- Khi bếp bắt đầu nấu, TV4 chọn đơn đủ điều kiện theo Test Contract, trừ đúng lượng đã giữ khỏi `self.stock`, xóa phần giữ và cập nhật trạng thái đơn trong cùng bước.
- Khi khách rời mà đơn còn nguyên liệu đang giữ, TV3 giải phóng phần giữ. `self.stock` chỉ thay đổi ở thời điểm bếp tiêu nguyên liệu.

## Phân vùng trong `quan.py`

- **TV3** phụ trách khởi tạo khách từ fixture, lịch khách đến, chọn món, giữ nguyên liệu và xử lý hết kiên nhẫn.
- **TV4** phụ trách bếp, tương tác tại bếp hoặc bàn, bưng món, phục vụ, ăn, thanh toán và kết ca.
- Mỗi người viết logic trong các hàm riêng. Hai người thống nhất thứ tự gọi trong `step()` theo mục F và cử một người ghép các lời gọi. Cần xác nhận cách xử lý khi khách hết kiên nhẫn đúng tick người chơi tương tác.

## Kiểm tra khi tích hợp

1. Khách gọi món, bếp nhận đơn và trừ đúng nguyên liệu một lần.
2. Khách rời trước khi bếp nhận đơn, giải phóng phần giữ để nguyên liệu khả dụng trở lại.

## Phản hồi TV4

### Đồng ý

- Dữ liệu dùng chung: `self.customers`, `customer["reserved"]`, `order_id`, `order_tick`, mã món, trạng thái đơn, `patience_ticks_left`.
- Cách giữ, trừ, nhả nguyên liệu: `self.stock` chỉ đổi khi bếp nhận đơn; TV4 trừ kho và xóa `reserved` trong cùng bước; TV3 nhả `reserved` khi khách rời.
- Phân vùng code và mỗi người viết logic trong hàm riêng.

### Đề xuất thêm

1. **Người ghép `step()`:** TV4 ghép, vì phần lớn lời gọi (bếp, ăn, interact, kết ca) thuộc Lát 4. TV3 review diff `step()` trước khi tích hợp.
2. **Thứ tự trong `step()`** (theo gợi ý của starter, đối chiếu lại với mục F trước khi chốt):
   1. Đồng hồ: `time_left_ticks`.
   2. TV3: giảm kiên nhẫn, khách hết kiên nhẫn thì rời (`customer_left`) và nhả `reserved`.
   3. TV4: bếp đếm `cook_ticks_left`, chín thì sang `ready` (`dish_ready`).
   4. TV4: khách ăn đếm thời gian, ăn xong thì trả tiền (`paid`).
   5. Di chuyển người chơi.
   6. TV4: tối đa một interact (cạnh lên), chọn theo khoảng cách, bếp trước bàn, rồi id.
   7. TV3: khách mới theo lịch, chọn món, giữ nguyên liệu (`customer_arrived` / `no_dish`).
   8. TV4: hết ca, xử lý khách còn lại và phát `quan_end`.
3. **Khách hết kiên nhẫn đúng tick người chơi bưng món tới:** nếu giữ thứ tự trên thì khách rời ở bước 2, interact ở bước 6 không còn khách để phục vụ, món vẫn trên tay. Cần đối chiếu mục F; nếu mục F không nói rõ thì ghi `docs/clarify.md` và nhờ PO hỏi.
4. **Ai xóa khách khỏi `self.customers`:** TV3 xóa khi khách rời; TV4 xóa khi khách trả tiền xong. Bàn được coi là có khách qua `customer["table_id"]` (như `snapshot()` hiện tại).
5. **TV4 cập nhật đơn ở các mốc:** bếp nhận đơn (đơn sang trạng thái đang nấu), bưng món (`hand` giữ món kèm `order_id`), phục vụ (khách sang trạng thái đang ăn). Tên trạng thái lấy đúng theo mục F.

### Cần TV3 xác nhận

- [ ] Danh sách trạng thái đơn và tên chính xác theo mục F.
- [ ] Kiên nhẫn có tiếp tục giảm khi đơn đang nấu hoặc khách đang ăn không.
- [ ] "Đơn chờ cũ nhất" mà bếp lấy: sắp theo `order_tick`, hòa thì theo `order_id`?
- [ ] Điều kiện boa: so `patience_ticks_left` tại lúc phục vụ hay lúc trả tiền với `tip_min_patience_ratio`; cách làm tròn (floor) và trường hợp đúng bằng ngưỡng.
- [ ] Hết ca: khách đang ăn / đang chờ xử lý thế nào, có phát `customer_left` hoặc `paid` trước `quan_end` không.

### Test TV4 sẽ viết

Dùng `scenario.customers[]` dựng sẵn khách và đơn để không phụ thuộc lịch khách đến của TV3:
nấu đúng `cook_s`, bưng khi tay đầy, phục vụ sai/đúng `order_id`, boa sát ngưỡng, thanh toán, kết ca.
Hai ca tích hợp ở mục trên TV3 và TV4 cùng chạy sau khi ghép.

## Phản hồi TV3

- Đồng ý TV4 ghép `step()` và TV3 review diff trước khi tích hợp. Dùng thứ tự tám bước ở trên để trao đổi, chờ đối chiếu mục F trước khi xác nhận thứ tự cuối cùng.
- Đồng ý TV3 xóa khách khi khách rời và nhả phần giữ còn lại. TV4 xóa khách khi đã thanh toán. Bàn xác định khách đang ngồi qua `customer["table_id"]`.
- Đồng ý TV4 cập nhật đơn khi bếp bắt đầu nấu, giữ `order_id` cùng món khi bưng và chuyển khách sang trạng thái ăn khi phục vụ. TV4 có thể chuẩn bị các ca kiểm thử bằng `scenario.customers[]`; hai ca tích hợp sẽ chạy chung sau khi ghép.
- Nếu mục F xác nhận giảm kiên nhẫn trước tương tác, ca hết kiên nhẫn đúng tick phục vụ sẽ phát `customer_left` trước lượt tương tác. Bàn đã trống và món vẫn trên tay. Quy tắc này đang chờ xác nhận.

### Trả lời năm mục cần xác nhận

1. **Trạng thái đơn.** Starter có nhắc `assigned` và `eating`. Cần mục F để xác nhận danh sách đầy đủ, tên trường và các bước chuyển trạng thái.
2. **Kiên nhẫn.** Theo kế hoạch nhóm, khách mới bắt đầu giảm kiên nhẫn từ tick kế tiếp. Cần mục F để xác nhận có tiếp tục giảm khi đang nấu hoặc đang ăn không.
3. **Đơn chờ cũ nhất.** TV3 đồng ý đề xuất lấy `order_tick` nhỏ nhất trong các đơn đủ điều kiện, hòa thì theo `order_id`. Chờ đối chiếu mục F trước khi áp dụng.
4. **Tiền boa.** Kế hoạch nhóm ghi dùng `floor`. Cần mục F để xác nhận công thức, thời điểm lấy kiên nhẫn và cách xử lý đúng bằng ngưỡng.
5. **Hết ca.** Cần mục F để xác nhận cách xử lý khách đang chờ và đang ăn, cùng thứ tự `customer_left`, `paid` và `quan_end`.

Chưa có bản đầy đủ mục F trong workspace. Các câu hỏi đã được ghi trong `docs/clarify.md` để PO đối chiếu với PRD-0/Test Contract v1.0.
