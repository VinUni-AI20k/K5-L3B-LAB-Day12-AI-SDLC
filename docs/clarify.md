# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 10:00 | Thứ tự ưu tiên khi có nhiều đối tượng (bếp, bàn) trong bán kính tương tác? | Ưu tiên đối tượng khoảng cách gần nhất -> bếp trước bàn -> ID nhỏ hơn. Nếu đối tượng được chọn không tương tác được thì bỏ lượt (không xét đối tượng kế tiếp). | PO (Đỗ Việt Anh) |
| 2 | 2026-11-21 10:05 | Cơ chế chọn món ngẫu nhiên cho khách mới khi vào quán? | Chỉ chọn trong các món mà tồn khả dụng (tồn vật lý trừ phần giữ chỗ) đủ nấu. Sắp xếp món theo Unicode và chọn đều qua luồng RNG `customer_dish`. Nếu không món nào đủ thì phát `no_dish` và khách không vào bàn. | PO (Đỗ Việt Anh) |
| 3 | 2026-11-21 10:10 | Xử lý trạng thái khi khách hết kiên nhẫn hoặc khi hết ca tối? | Hết kiên nhẫn: trừ 0.5 uy tín, giải phóng giữ chỗ, hủy món trên bếp/tay nếu có (nguyên liệu đã nấu không hoàn lại). Hết ca: khách đang ăn trả tiền ngay, khách đang chờ rời quán với lý do closing và không bị trừ uy tín. | PO (Đỗ Việt Anh) |
