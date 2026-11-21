# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | PRD-0 mục E/F quy định tên và payload sự kiện khách đến, `no_dish`, `customer_left`, thứ tự tick và cách chọn món thế nào? | Giảm kiên nhẫn đầu bước, xét khách rời sau tương tác, rồi xét khách mới nếu còn giờ. Chọn đều theo seed trong các món khả thi đã sắp theo ID. `customer_arrived` dùng `order_id,table_id,dish_id`, `no_dish` có data rỗng, `customer_left` dùng `order_id,table_id,reason,reputation`. | PRD-0 E/F |
| 2 | 2026-11-21 | PRD-0 mục D/F mô tả `stock`, `reserved` và các trạng thái đơn trong scenario như thế nào? | `stock` là tồn vật lý. Kho khả dụng bằng tồn vật lý trừ tổng `reserved`. Đơn `reserved` suy ra phần giữ từ công thức khi thiếu trường này. Khi bắt đầu nấu, bếp trừ phần giữ khỏi tồn vật lý, xóa phần giữ, chuyển đơn sang `assigned` và gắn món với `order_id`. | PRD-0 D/E/F |
| 3 | 2026-11-21 | Ticket-02: P2-03 cung cấp màn hiện tại, snapshot Day, kết quả Shop/Pause như thế nào cho web? P2-02 phát tên event trúng cá sấu nào? | Đang dùng payload web đề xuất trong `docs/verification/phase-2.md` để phát triển UI bằng fixture. Chờ P2-02/03 đối chiếu trước khi nối live thật. | PO + P2-02/03 |
