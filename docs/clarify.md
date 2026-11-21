# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | PRD-0 mục E: tên sự kiện khi khách đến quán là gì, và `data` gồm trường nào? | Chưa có tên trong repo. Giả định tạm: B (quán) tự đặt tên rồi ghi vào `docs/contracts/README.md`. Chờ PO xác nhận. | PO (chờ trả lời) |
| 2 | 2026-11-21 | Scenario `quan.hand`: là id món (chuỗi) hay object? Có giá trị `null` khi tay trống không? | Chưa rõ. Giả định tạm: scenario không kiểm `hand` để khỏi từ chối nhầm; kiểm sau khi PO trả lời. | PO (chờ trả lời) |
| 3 | 2026-11-21 | PRD-0 mục D: đơn `assigned` "đúng một món" nghĩa là khách có trường nào chứa món, và tên trường là gì? | Chưa có tên trường nên `scenario.py` chưa kiểm. Giả định tạm: bỏ qua cho tới khi có PRD mục D. | PO (chờ trả lời) |
| 4 | 2026-11-21 | Khách `eating` thiếu giá hoặc boa: các trường giá và boa tên gì, thiếu thì mã thoát 2 hay lấy từ menu? | Chưa rõ. Giả định tạm: chưa kiểm; khi nấu xong lấy giá từ `menu.<món>.price`. | PO (chờ trả lời) |
| 5 | 2026-11-21 | Khách giữ chỗ nguyên liệu khi kho nạp từ `--inventory`: ai kiểm vượt kho, bước nạp scenario hay lúc sim chạy? | Giả định tạm: nạp scenario chỉ so khi scenario tự khai `stock`; với `--inventory` thì B so lúc dựng sim và báo `BadInput` (mã 2). | PO + B (chờ xác nhận) |
