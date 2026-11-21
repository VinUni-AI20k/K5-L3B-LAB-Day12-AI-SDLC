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
| 9 | Phase 2 | Nhóm 5 người cần ≥ 1 mở rộng: bật cái nào, `burn_s` lõi là `null` thì sao? | Bật **burn**: `"extensions": ["burn"]`, `quan.burn_s: 20` (Ticket 4.1: burn = `burn_s` hữu hạn + khai mã). `null` chỉ áp khi không khai mở rộng. Test giả định `null` tự dựng tuning lõi. | PO + nhóm (contracts I-1) |
| 10 | Phase 2 | Snapshot cá có xuất `age_ticks` không? Ticket chỉ nói scenario có. | Có: `fish[] = {id, pos, kind, heading_deg, age_ticks}`; trường thừa không vỡ UI, giúp kiểm lịch đổi hướng. | PO + mhoo40 (contracts I-2) |
| 11 | Phase 2 | Cá Sấu có dùng số ngẫu nhiên? | Không: Ticket 1.2 chỉ mô tả luật cố định (patrol/chase/recoil), không nhắc seed. | PO + s0ra1n0 (contracts I-3) |
| 12 | Phase 2 | Mode `day` đặt lại id/RNG mỗi Ngày? | Không: một `Streams` + một `IdAllocator` cho cả lượt; id khách nối tiếp qua Ngày (Ticket D: "trong lượt"). | PO + tiepnnk01-10 (contracts I-4) |
| 13 | Phase 2 | Cá Sấu xét `patrol` ↔ `chase` theo khoảng cách trước hay sau khi nó di chuyển trong bước? | Giả định: **trước** khi di chuyển (người chơi đã di chuyển xong). Hit xét sau khi cả hai di chuyển như Ticket nói. | s0ra1n0 (lát 1) |
| 14 | Phase 2 | `recoil_dist` là tổng quãng lùi hay mỗi bước? Hướng ban đầu cá "theo seed" lấy thế nào? | `recoil_dist = 2.0` là tổng trong `recoil_ticks = 60` (2/60 m/bước, khớp Ticket). Hướng cá: tạm số nguyên 0–359 qua stream `fish_spawn`, lát 2 chốt. | s0ra1n0 (lát 0/1) |
