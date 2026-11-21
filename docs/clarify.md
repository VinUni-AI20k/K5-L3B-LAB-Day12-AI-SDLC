# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11 10:30 | Danh sách mục mở rộng của nhóm 5 người nằm ở đâu, nhóm chọn mục nào? | Anh Năm chưa trả lời được (lab board báo `not_granted`). Giả định: Phase 1 chỉ làm lõi đúng; hỏi lại khi mở Phase 2 | C (PO) |
| 2 | 21/11 10:30 | Tới lượt khách đến mà kho khả dụng không đủ cho món nào: khách vẫn ngồi (đơn `unfulfillable`) hay chỉ phát `no_dish`? | Anh Năm chưa trả lời được. Giả định: chỉ phát `no_dish{}`, không tạo khách, không chiếm bàn (khớp `docs/contracts/README.md` mục 2) | C (PO) |
| 3 | 21/11 10:30 | Hết ca: khách có đơn đang nấu (`assigned`, chưa phục vụ) rời thế nào? | Anh Năm chưa trả lời được. Giả định: mọi khách `waiting` (kể cả `assigned`) rời với `reason: "closing"`, không trừ uy tín; món của đơn bị bỏ qua `_drop_order`, nguyên liệu đã nấu không hoàn lại | C (PO) |
| 4 | 21/11 | Lát 2: nút hái ở bước k mọc lại sau đúng bao nhiêu bước? Khung giảm `regrow_ticks` ở đầu mỗi bước nên `node_regrown` phát ở tick k+1+1200 (hái ở bước 0 thì tick 1201) | Giả định: `regrow_s*60` bước kể từ bước kế tiếp, test khóa tick 1201. Chờ PO xác nhận | PO |
| 5 | 21/11 | Lát 2: hồi chiêu `catch` 0,5 giây tính từ tick bắt hay tick sau? Hiện bắt ở bước k thì bắt lại được ở bước k+30 (bấm lúc còn 29 bước thì chặn) | Giả định như trên, test khóa mốc 29 chặn và 30 được. Chờ PO xác nhận | PO |
| 6 | 21/11 | Lát 2: `gather.amount` có luôn bằng `node_yield` không, hay có hái một phần khi giỏ gần đầy? | Giả định: hái trọn `node_yield` hoặc `hold_full`, không hái một phần (cá cũng vậy: đủ chỗ cho cả `fish_yield` mới bắt). Chờ PO xác nhận | PO |
