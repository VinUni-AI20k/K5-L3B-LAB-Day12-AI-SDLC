# Kế hoạch Phase 2 — phần Thành viên 4

## Bổ sung lượt TV2 — Gather v1.1

- Nguồn: gói `02_TV2_Ducbaynao`, lấy phiên bản cuối mỗi file qua ba manifest. Tích hợp cá bơi/sinh và Cá Sấu M1/M2, hỗ trợ `day` và nâng cấp truyền vào `GatherSim`, cập nhật validator Gather, danh mục kho, HUD và tuning v1.1.
- Giữ phần Quán và các test kỳ vọng hiện hành; không nhập validator Quán từ gói vì thuộc bản nền khác. Fixture test Quán được khóa số bàn/khách phát sinh để không phụ thuộc số bàn mặc định mới.
- TV1 tiếp nối vòng lặp D1–D5, shop và pause. Hiện CLI vẫn chỉ có `gather|quan`, mặc định Gather là ngày 1; M2/ngày 3 được kiểm tra qua API sim. Chưa xác nhận toàn Phase 2 hoặc gắn tag.
- Chạy `python docs/proof/phase-2/member-2/verify.py`; xem [bàn giao TV2](../proof/phase-2/member-2/README.md).

## Phần Thành viên 4 giữ lại

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
