# Kế hoạch Phase 2 — phần Thành viên 4

**Phụ trách:** Vũ Văn Bình (`hnib1908`), `sim/quan`, PO.

| Lượt | Việc | Tiêu chí |
|---|---|---|
| 10 | Lịch khách đến và xếp bàn | Đúng tick từ tuning, chọn bàn trống theo thứ tự ID, bỏ qua lượt khi đầy bàn, cấp ID tiếp sau fixture. |
| 11 | Chọn món và giữ chỗ | Dùng kho khả dụng sau khi trừ `reserved`, chọn món tất định theo seed, phát `no_dish` khi không đủ nguyên liệu và để bàn trống. |
| 12 | Hết kiên nhẫn và bàn giao | Đếm từ tick sau khi vào bàn, phát `customer_left` đúng lúc, giải phóng bàn và nguyên liệu, cập nhật uy tín trong giới hạn. |

- Dùng `tests/test_quan_customers.py` và [ma trận kiểm chứng](../verification/phase-2.md) để kiểm tra phần TV4.
- `stock` là số lượng vật lý. TV5 khi bắt đầu nấu cần trừ nguyên liệu khỏi `stock` và xóa đúng `reserved` của đơn đã dùng. Khách đang `eating` tiếp tục chiếm bàn; bộ đếm kiên nhẫn dừng.
- `chonoi/web/index.html` đọc tên món và kiên nhẫn theo snapshot của hợp đồng nhóm. Fixture có thể dùng tên trường cũ `dish_id` và `patience_ticks_left`.
- Integrator kiểm tra kết quả sau khi tích hợp PR Phase 1 và xác nhận đầy đủ phạm vi trên lab board trước khi gắn `phase-2`.
