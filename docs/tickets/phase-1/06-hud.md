# 06: HUD hai buổi

**What to build:** Người chơi nhìn màn hình là biết mình đang có bao nhiêu thời gian, oxy, Máu, giỏ; tối đến thì biết kho còn gì, ai đang gọi món, ai sắp bỏ đi, bếp đang nấu gì, tay đang cầm gì, tiền và uy tín bao nhiêu.

**Blocked by:** None (can start immediately)

**Status:** done (ready-for-review)

- [x] Buổi sáng hiện: thời gian còn lại (đổi màu < 30s), thanh oxy (đổi màu khi gần cạn < 25%), Máu (tim đỏ/rỗng), số món/`hold_capacity`, danh sách món trong giỏ kèm số lượng, nhắc phím ngữ cảnh khi vào tầm nút (hái rau)/đàn cá (bắt cá)/bến tàu (cập bến).
- [x] Buổi tối hiện: `stock` (kho dự trữ nguyên liệu trực quan), khách đang ngồi kèm món gọi + thanh kiên nhẫn (xanh/vàng/đỏ), trạng thái bếp + thời gian nấu đếm ngược, món trên tay, tiền, uy tín, thời gian còn lại, nhắc phím ngữ cảnh (bếp / bàn).
- [x] Thiếu trường nào thì bỏ qua trường đó, không văng lỗi (client chạy được khi luật chưa xong, `null-safe`).
- [x] Không che vùng chơi: chữ/thanh HUD nằm ngoài vùng tương tác quanh nhân vật, bo góc thanh lịch, alpha lớp trang trí thấp khi đi qua vùng đó.
- [x] Màn kết thúc hiện lý do (`time`/`docked`/`fainted`) và bảng điểm chi tiết (tiền, uy tín, điểm số, sản lượng); nút chơi lại hoạt động cả click chuột lẫn phím R.
- [x] Không thêm mã nào vào `chonoi/` hay đổi snapshot; headless vẫn cho JSONL giống từng byte.
