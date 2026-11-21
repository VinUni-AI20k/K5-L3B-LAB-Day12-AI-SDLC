# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-04 | 2026-11-21 | Khi vừa cạn oxy, tick đó có tính ngạt không? `invuln_ticks` có chặn ngạt không? | Tính tick vừa cạn là tick ngạt đầu tiên. `invuln_ticks` được thêm ở v1.1 và không chặn ngạt. | PRD-0 mục D, F và TICKET-02 mục 1.1, 4.3 |
| P1-05 | 2026-11-21 | Khi giỏ thiếu chỗ hoặc bắt trượt thì xử lý thế nào? Hai đàn cá cùng khoảng cách thì chọn đàn nào? | Cần đủ chỗ cho toàn bộ sản lượng. Thiếu chỗ phát `hold_full` với `action`, id mục tiêu, `required` và `free`. Chỉ bắt thành công mới đặt hồi chiêu. Cùng khoảng cách chọn id nhỏ nhất theo quy tắc hậu tố số ASCII. | PRD-0 mục D, E, F |
