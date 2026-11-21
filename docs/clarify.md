# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 2 | Khách đang chờ (chưa nấu) thì `base_price`, `tip` là gì? PRD chỉ nói "khách eating khai base_price, tip đã chốt". | Giả định: `null` tới lúc chốt giá (`cook_started`) / chốt boa (`served`). | lát 3 (chờ PO hỏi Anh Năm) |
| 2 | Phase 2 | `stoves[].dish` là id món hay payload món? | Giả định: payload `{order_id, dish_id, base_price}` giống `hand`, vì PRD kiểm "bếp và tay giữ cùng đơn". Khách rời thì bỏ món có `order_id` trùng. | lát 3 + lát 4 |
| 3 | Phase 2 | Khách hết kiên nhẫn đúng tick hết ca: rời `patience` (trừ uy tín) hay `closing`? | Giả định: `closing`, không trừ uy tín — PRD: "nếu ca còn giờ" mới rời vì kiên nhẫn. | lát 3 |
