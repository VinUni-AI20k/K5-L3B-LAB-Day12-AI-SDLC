# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 2 | Khách đang chờ (chưa nấu) thì `base_price`, `tip` là gì? PRD chỉ nói "khách eating khai base_price, tip đã chốt". | Giả định: `null` tới lúc chốt giá (`cook_started`) / chốt boa (`served`). | lát 3 (chờ PO hỏi Anh Năm) |
| 2 | Phase 2 | `stoves[].dish` là id món hay payload món? | Giả định: payload `{order_id, dish_id, base_price}` giống `hand`, vì PRD kiểm "bếp và tay giữ cùng đơn". Khách rời thì bỏ món có `order_id` trùng. | lát 3 + lát 4 |
| 3 | Phase 2 | Khách hết kiên nhẫn đúng tick hết ca: rời `patience` (trừ uy tín) hay `closing`? | Giả định: `closing`, không trừ uy tín — PRD: "nếu ca còn giờ" mới rời vì kiên nhẫn. | lát 3 |
| 4 | Phase 2 | `day.upgrades` trong scenario là cấp đã mua; có hiệu lực ngay Ngày 1 không? | Giả định: có — Ngày 1 được dựng sau khi nạp scenario nên `active_upgrades` = `upgrades` khai. Cấp mua trong Shop chỉ hiệu lực từ Ngày kế. | lát 5 |
| 5 | Phase 2 | Đổi pha có bắt buộc ghi thêm snapshot không? | Giả định: không. Snapshot vẫn theo v1.0 (tick 0, bội số `--snapshot-every`, tick dừng); snapshot nào rơi vào tick đổi pha thì ghi pha mới với `phase_tick: 0`. | lát 5 |
| 6 | Phase 2 | `buy` của mở rộng chưa bật (vd `weapon`): "bỏ qua" (4.2) hay `buy_failed unknown` (4.2 "lệnh không hỗ trợ")? | Giả định: trong Shop phát `buy_failed {reason: unknown}`; ngoài Shop thì bỏ qua (sai pha). | lát 5 (chờ PO hỏi Anh Năm) |
| 7 | Phase 2 | `day_plan`, `shop` đặt ở đâu trong manifest? | Đặt trong `tuning` (cùng cấp gather/quan/menu) theo bảng "Phạm vi" mục 4.1; `extensions` mới ở gốc. | lát 5 |
| 8 | Phase 2 | Khách fixture trong mẫu `quan` của day gọi món ngoài kế hoạch Ngày? | Mã 2 khi mở quán Ngày đó ("món thuộc kế hoạch được kiểm trên kho thực lúc mở quán"). JSONL đã ghi tới tick đó. | lát 5 |
