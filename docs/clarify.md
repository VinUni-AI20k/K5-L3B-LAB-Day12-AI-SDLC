# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-04 | 2026-11-21 | Khi vừa cạn oxy, tick đó có tính ngạt không? `invuln_ticks` có chặn ngạt không? | Tạm tính tick vừa cạn là tick ngạt đầu tiên. Trừ máu theo `choke_interval_ticks`, kể cả khi `invuln_ticks` còn dương. | Chờ Lương (PO) xác nhận |
| P1-05 | 2026-11-21 | Khi giỏ thiếu chỗ hoặc bắt trượt thì xử lý thế nào? Hai đàn cá cùng khoảng cách thì chọn đàn nào? | Tạm yêu cầu đủ chỗ cho toàn bộ sản lượng. Nếu thiếu thì giữ nguyên mục tiêu và giỏ, phát `hold_full` với `source` là `node` hoặc `fish`. Chỉ bắt thành công mới bắt đầu hồi chiêu. Cùng khoảng cách thì chọn id nhỏ theo thứ tự của `ids.sort_by_id`. | Chờ Lương (PO) xác nhận |
