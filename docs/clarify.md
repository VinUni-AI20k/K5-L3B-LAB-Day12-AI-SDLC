# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11 10:30 | Danh sách mục mở rộng của nhóm 5 người nằm ở đâu, nhóm chọn mục nào? | Anh Năm chưa trả lời được (lab board báo `not_granted`). Giả định: Phase 1 chỉ làm lõi đúng; hỏi lại khi mở Phase 2 | C (PO) |
| 2 | 21/11 10:30 | Tới lượt khách đến mà kho khả dụng không đủ cho món nào: khách vẫn ngồi (đơn `unfulfillable`) hay chỉ phát `no_dish`? | Anh Năm chưa trả lời được. Giả định: chỉ phát `no_dish{}`, không tạo khách, không chiếm bàn (khớp `docs/contracts/README.md` mục 2) | C (PO) |
| 3 | 21/11 10:30 | Hết ca: khách có đơn đang nấu (`assigned`, chưa phục vụ) rời thế nào? | Anh Năm chưa trả lời được. Giả định: mọi khách `waiting` (kể cả `assigned`) rời với `reason: "closing"`, không trừ uy tín; món của đơn bị bỏ qua `_drop_order`, nguyên liệu đã nấu không hoàn lại | C (PO) |
