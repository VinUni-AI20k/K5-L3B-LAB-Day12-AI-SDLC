# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Đề ghi nhóm 4–6 người, nhóm F7 có 7 người. Có được giữ 7 người không? (`tools/check_team.py` sẽ cảnh báo "phải từ 4 đến 6", CI chỉ cảnh báo, không chặn) | Giả định: giữ 7 người, `team_size` = 7. Chờ giảng viên xác nhận. | PO (nganhduong123) |
| 2 | 2026-11-21 (P2) | Ticket-02 §3: nhóm 5 làm ≥ 1 mở rộng, nhóm 6 làm ≥ 2. Nhóm 7 người cần bao nhiêu mục? | Giả định: ≥ 2 mục (như nhóm 6), làm sau khi lõi xanh. Chờ giảng viên xác nhận. | PO |
| 3 | 2026-11-21 (P2) | DayIntro (tự chuyển sau 4 s), EveningIntro, DayResult có nằm trong luồng sim/headless không? Ticket chỉ liệt kê `phase` ∈ gather/quan/shop. | Giả định: là màn hình của bản chơi. Client giữ đồng hồ đứng yên bằng nút `pause` trong lúc hiện intro; headless không có các màn này. | PO |
| 4 | 2026-11-21 (P2) | HUD quán "kho khả dụng": `stock` trong snapshot đã trừ phần khách đang giữ (`reserved`) chưa? | Giả định: `stock` là kho khả dụng (đã trừ phần giữ). Lát 3 xác nhận khi chốt hợp đồng. | PO + Quoosc |
| 5 | 2026-11-21 | Lát G2 yêu cầu N5 [76,0], N6 [90,0] và cá kèo yield 2. Nhóm có đồng ý mở khóa dữ liệu Gather và mở rộng các loại nguyên liệu hợp lệ không? Nếu cá kèo xuất hiện mặc định thì đàn nào, ở đâu? | Chờ PO chốt. | PO (nganhduong123) |
| 6 | 2026-11-21 (P2) | Ticket-02 quy định tốc độ, độ sâu tối thiểu, chu kỳ và góc đổi hướng, lịch sinh đàn và sự kiện sinh cá thế nào? | Mô phỏng đã đọc tuning tùy chọn. Chờ đối chiếu Ticket-02 đầy đủ và chốt tên khóa, quy tắc và giá trị trước khi đưa vào contract chung. | PO + Integrator (invzble-z) |
| 7 | 2026-11-21 | Khi nào bàn giao kho từ buổi sáng sang quán? | Hợp nhất mode `day`: khi buổi Gather kết thúc bằng cập bến, hết giờ hoặc ngất, kho được bàn giao sang Quan ngay trong cùng tiến trình. | PO |

## Draft for PO — Q3 D-01..D-09 (2026-11-21)

The local checkout and feature source review contain no full Phase 1 PRD-0/Test Contract. Please confirm the authoritative source and resolve: (D-01) customer states/defaults and assigned/eating order link; (D-02) random_customers default and elapsed schedule boundary; (D-03) full-table retry/drop policy; (D-04) required RNG stream/selection; (D-05) stock/reservation snapshot and consume/release moments; (D-06) same-tick timer/interaction/end ordering; (D-07) customer_left payload and penalty owner; (D-08) no_dish event/terminal condition; (D-09) fixture and order/stove/hand cross-validation. Current implementation uses the explicit PROPOSED choices in docs/proof/phase-1/q3/README.md; they do not constitute official acceptance.

## Phase 2 — giao diện kế hoạch khách (chờ PO và integrator)

Mock UI biểu diễn `day_plan.dishes` là mapping món sang số lượng. Cần chốt schema chính thức, số lượng là hạn mức hay chỉ là mục tiêu, cách liên kết món đang cầm với khách. Kế hoạch phân công chỉ định `menu_filter` cho `QuanSim`; DaySim cần truyền danh sách món qua tham số này. Xem `docs/proof/phase-2/quoc.md`.

Chờ PO xác nhận: `no_dish` phát khi bàn đầy hay khi không còn món hợp lệ, và có kết thúc ca không; cơ hội đến hạn khi bàn đầy hoặc thiếu món được bỏ hay thử lại; `order_tick` mặc định của fixture; khách `ordered` có tiếp tục mất kiên nhẫn khi nấu; snapshot `stock` là kho vật lý hay kho sau reservation; món đang nấu xử lý thế nào khi khách rời. Những lựa chọn hiện hành chỉ là tạm thời, chưa phải AC chính thức.
