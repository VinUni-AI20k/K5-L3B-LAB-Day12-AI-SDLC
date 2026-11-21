# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 08:15 | Khi hết ca (closing), khách còn đang ngồi ăn hoặc đang chờ thì xử lý tiền và uy tín thế nào? | Khách đang ăn được tính tiền ngay (`paid` với lý do `closing`); khách đang chờ thì rời quán (`customer_left` với lý do `closing`) và KHÔNG bị trừ uy tín. | PRD-0 mục F |
| 2 | 2026-11-21 08:25 | Phím hái (`interact`) và phím bắt cá (`catch`) có dùng chung dưới nước được không? | Không. `interact` hái nút chỉ dùng khi ở mặt nước (`d <= 0.5`) hoặc tại bến; `catch` bắt cá chỉ hoạt động khi lặn dưới nước (`d > 0.5`) và hết cooldown. | PRD-0 mục F |
| 3 | 2026-11-21 08:35 | Schema file kho khi ngất (`fainted`) có ghi file không? | Khi ngất, phát sự kiện `faint` với lost LIFO, sau đó `gather_end` với kho rỗng `{"items": {}}`. File kho ghi ra là object rỗng. | Test Contract v1.0 |
