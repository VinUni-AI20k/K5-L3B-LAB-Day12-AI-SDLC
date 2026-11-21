# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-L2-1 | 2026-11-21 | Cooldown bắt cá có bắt đầu khi bắt hụt hoặc giỏ thiếu chỗ không? | Tạm triển khai chỉ bắt đầu khi `fish_caught`; hụt/`hold_full` giữ nguyên đàn và không đặt lại cooldown. Đã hỏi người dùng, chờ PO đối chiếu PRD-0. | Chờ PO (Minh) |
| P1-L2-2 | 2026-11-21 | Payload sự kiện Lát 2 là gì? Repo chưa có bản PRD-0 đầy đủ và bảng sự kiện trong `docs/contracts/` chưa được chốt. | Đã đối chiếu hợp đồng Integrator mới trên main và cập nhật code/test: `gather {node_id, kind, amount}`, `fish_caught {fish_id, kind, yield}`, `hold_full {required, free}`. Không sửa hợp đồng khóa. | Theo docs/contracts/README.md của Diệp |
| 1 | 21/11/2026 | Khách đến nhưng không có món đủ nguyên liệu có chiếm bàn không? | Giả định: Không tạo khách, không chiếm bàn, phát `no_dish`. | PO – Minh |
| 2 | 21/11/2026 | Nhiều khách đến cùng tick thì thứ tự xử lý thế nào? | Giả định: Xử lý theo ID khách tăng dần. | PO – Minh |
| 3 | 21/11/2026 | ID khách mới có định dạng bắt buộc không? | Giả định: Sinh ID C1, C2... không trùng fixture. | Minh + Diệp |
| 4 | 21/11/2026 | Khách rời đi khi món đã trên tay thì xử lý thế nào? | Theo Test Contract: Hủy món, không hoàn nguyên liệu đã tiêu thụ. | Minh + Diệp |
| 5 | 21/11/2026 | Scenario có khách và đơn sẵn thì có tạo lại đơn không? | Không tạo lại; giữ nguyên fixture, suy ra reserved khi thiếu theo contract. | Minh |
| 6 | 21/11/2026 | `hand` và `stove.dish` trong snapshot quán có dạng gì? Khóa `data` của `cook_started`/`dish_ready`/`dish_picked`/`served`/`paid` là gì? | Đã đối chiếu PRD-0 mục D: `hand = null` hoặc `{"order_id","dish_id","base_price"}`; `stoves[].dish = null` hoặc `{"dish_id","order_id"}`; cả hai dùng đúng `order_id = id khách`. | Diệp → PO – Minh |
| 7 | 21/11/2026 | `tip_reputation` (0.2) cộng uy tín lúc nào? Interact khi đối tượng gần nhất không làm được gì thì có thử đối tượng kế tiếp không? | Giả định (lát 4): có boa (kiên nhẫn ≥ `tip_min_patience_ratio`) → `+tip_reputation` lúc `paid`, kẹp [min, max]. Interact chỉ xét đối tượng gần nhất theo (khoảng cách, bếp trước bàn, id); không làm được thì bỏ qua, không thử đối tượng khác. **Chờ PO đối chiếu PRD-0.** | Diệp → PO – Minh |
