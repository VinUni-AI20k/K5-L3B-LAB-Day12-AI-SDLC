# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 P1 0:10 | Chọn món "đều theo seed" dùng stream nào của `Streams`, và rút một số mỗi lần khách đến hay chỉ khi có ≥ 2 món đủ kho? | Giả định: stream riêng tên `customers`, rút `randrange(len(ứng viên))` mỗi lần có khách đến và có ≥ 1 món đủ kho (danh sách ứng viên sắp id món theo Unicode). Chờ Anh Năm xác nhận. | PO (tạm) |
| 2 | 2026-11-21 P1 0:10 | `data` của `oxygen_empty`, `gather`, `fish_caught`, `customer_arrived`, `no_dish` gồm những trường nào? PRD-0 mục E chỉ nêu rõ `dive/surface`, `choke`, `faint`, `hold_full`, `cook_started`. | Giả định theo `docs/contracts/README.md` mục 2 (đánh dấu [giả định]). Có câu trả lời thì sửa hợp đồng và báo lát 1–4. | PO (tạm) |
| 3 | 2026-11-21 P1 0:10 | Bước cuối ca quán: xử lý khách mới / interact / kiên nhẫn trước rồi mới trả `closing`, hay `time_left_ticks` về 0 là chốt ca ngay đầu bước? Một khách vừa hết kiên nhẫn đúng tick hết ca thì rời `patience` hay `closing`? | Giả định: chạy đủ bước bình thường, cuối bước mới xử lý `closing` rồi `quan_end`; hết kiên nhẫn cùng tick → `patience` (trừ uy tín). Chờ Anh Năm xác nhận. | PO (tạm) |
| 4 | 2026-11-21 P1 0:55 | Trạng thái câu 1–3 cuối Phase 1? | Chưa có trả lời từ Anh Năm; lát 3 đã dùng giả định câu 1 (chọn món qua `Streams`), lát 4 chưa gộp nên câu 3 vẫn mở. Mang sang Phase 2. | PO |
