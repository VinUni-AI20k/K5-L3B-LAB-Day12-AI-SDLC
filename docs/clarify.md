# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Đề ghi nhóm 4–6 người, nhóm F7 có 7 người. Có được giữ 7 người không? (`tools/check_team.py` sẽ cảnh báo "phải từ 4 đến 6", CI chỉ cảnh báo, không chặn) | Giả định: giữ 7 người, `team_size` = 7. Chờ giảng viên xác nhận. | PO (nganhduong123) |
| 2 | 2026-11-21 (P2) | Ticket-02 §3: nhóm 5 làm ≥ 1 mở rộng, nhóm 6 làm ≥ 2. Nhóm 7 người cần bao nhiêu mục? | Giả định: ≥ 2 mục (như nhóm 6), làm sau khi lõi xanh. Chờ giảng viên xác nhận. | PO |
| 3 | 2026-11-21 (P2) | DayIntro (tự chuyển sau 4 s), EveningIntro, DayResult có nằm trong luồng sim/headless không? Ticket chỉ liệt kê `phase` ∈ gather/quan/shop. | Giả định: là màn hình của bản chơi. Client giữ đồng hồ đứng yên bằng nút `pause` trong lúc hiện intro; headless không có các màn này. | PO |
| 4 | 2026-11-21 (P2) | HUD quán "kho khả dụng": `stock` trong snapshot đã trừ phần khách đang giữ (`reserved`) chưa? | Giả định: `stock` là kho khả dụng (đã trừ phần giữ). Lát 3 xác nhận khi chốt hợp đồng. | PO + Quoosc |
| 5 | 2026-11-21 | Lát G2 yêu cầu N5 [76,0], N6 [90,0] và cá kèo yield 2. Nhóm có đồng ý mở khóa dữ liệu Gather và mở rộng các loại nguyên liệu hợp lệ không? Nếu cá kèo xuất hiện mặc định thì đàn nào, ở đâu? | Chờ PO chốt. | PO (nganhduong123) |
