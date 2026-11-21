# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | P1 kickoff | `stoves[].dish` là payload món `{order_id,dish_id,base_price}` hay chỉ `dish_id`? | **Giả định:** payload món, giống `hand` (PRD D: "Bếp cooking có timer dương và món khớp đơn"). Chờ Anh Năm xác nhận. | C (chờ PO hỏi) |
| 2 | P1 kickoff | Đơn reserved trong scenario thiếu `reserved` mà kho không đủ công thức thì sao? | **Giả định:** mã 2 ("giữ quá tồn"). | C (chờ PO hỏi) |
| 3 | P1 kickoff | `customer_left.reputation` là uy tín trước hay sau khi trừ? | **Giả định:** sau khi trừ (và kẹp). | C (chờ PO hỏi) |
| 4 | P1 kickoff | Ở Phase 1 (không cháy món), đơn `unfulfillable` xuất hiện khi nào? | **Giả định:** chỉ dựng qua scenario; sim không tự tạo ở Phase 1. | C (chờ PO hỏi) |
| 5 | P1 kickoff | Scenario: `state` khách `eating` ⇔ `order_status` `served`? | **Giả định:** có, hai chiều (PRD D: "Khách eating phải là served"). | C |
