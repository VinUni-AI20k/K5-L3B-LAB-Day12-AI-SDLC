# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 1 | Giỏ còn thiếu chỗ cho cả mẻ (vd. còn 2 chỗ, bắt `ca_linh` được 3) thì thêm một phần hay không thêm gì? | Giả định: không thêm gì, phát `hold_full` | Lát 1, chờ PO xác nhận theo PRD-0 |
| 2 | Phase 1 | Tick đầu tiên oxy chạm 0 có tính là tick ngạt đầu tiên không? | Giả định: có (đếm ngay tick oxy về 0) | Lát 1, chờ PO xác nhận theo PRD-0 |
| 3 | Phase 1 | `data` của dive/surface/oxygen_empty/choke/faint/hold_full gồm những trường nào? | Giả định: xem `docs/contracts/events.md` | Lát 1, chờ PO xác nhận theo PRD-0 |
| 4 | Phase 1 | `invuln_ticks` dùng vào việc gì ở phase 1? | Giả định: chưa dùng, để cho phase sau | Lát 1, chờ PO xác nhận theo PRD-0 |
| 5 | Phase 1 | Mã tiêu chí chấp nhận trong PRD-0 là gì và còn tiêu chí nào ngoài phạm vi test công khai? | Tạm truy vết theo tên hành vi và test trong repo. Chờ bản PRD-0 để bổ sung mã và phần còn thiếu. | PO đối chiếu Lab Board |
| 6 | Phase 1 | Khi khách bỏ đi, lát nào hoàn nguyên liệu giữ chỗ? Thứ tự xử lý khi khách hết kiên nhẫn cùng bước bấm phục vụ là gì? | Dùng schema khách hiện có để tích hợp. Chờ xác nhận thứ tự tick và trách nhiệm giữa hai lát trước khi kết luận kiểm thử. | PO, developer lát 3 và lát 4 |
