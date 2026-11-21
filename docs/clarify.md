# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11/2026 | Dùng bộ số và công nghệ nào cho Phase 1? | Giữ preset v1.0 và starter Python/Canvas. Hai lát làm song song với mẫu kho đếm. | Khôi đã xác nhận kickoff `d8d77a0` |
| 2 | 21/11/2026 | Tích hợp khi các lát hoàn thành khác lúc thế nào? | Dùng nhánh riêng, review và merge commit. Khôi báo SHA khi phần phụ thuộc đã vào `main`. | Khôi đã xác nhận kickoff `d8d77a0` |
| 3 | 21/11/2026 | Phase 2 bàn giao kho và trạng thái xuyên Ngày thế nào? | Runner giữ tiến trình và trao kho đếm trong bộ nhớ khi chạy `day`. Hai CLI độc lập tiếp tục dùng file kho. Đã kiểm cả hai cách. | Khôi review bản tích hợp |
| 4 | 21/11/2026 | Khi nào bật contract v1.1? | Bật ở PR cuối của Khôi trên nền `b2719e6`, sau khi Gather và Quán đã gộp. Giữ các điều chỉnh tích hợp trong phạm vi Test Contract. | Khôi review bản tích hợp |
| 5 | 21/11/2026 | Phase 3 đưa schema kho cá thể vào main theo thứ tự nào? | PR #7 gộp adapter của Diên, PR #8 gộp Quán của Nhân. PR cuối nối adapter vào Gather, CLI và vòng ngày, rồi bật v1.2. | Thứ tự do Khôi xác nhận, bản tích hợp chờ review |
