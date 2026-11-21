# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 2 | `day_plan`, `shop.upgrades` và payload event chính thức ở Mục 4.4 sẽ dùng khóa và kiểu nào? | UI hiện dùng fixture v1.1 riêng cho 5 ngày. Repo tích hợp vẫn khai v1.0. | Chờ PO / Integrator |
| 2 | Phase 2 | Live adapter giữ đồng hồ pha trong lúc hiện DayIntro, EveningIntro và DayResult bằng giao diện nào? | Bản xem dùng `awaiting` trong snapshot web và xác nhận tiếp tục qua adapter. Cần chốt giao diện với backend v1.1. | Chờ Integrator |
| P1-01 | 2026-11-21 | Người chơi chọn Chơi trọn ngày trên trình duyệt thì hai mode headless nối kho thế nào? | Live dùng `/continue` để chuyển sang Quán sau khi Gather chốt kho. Kiểm chứng headless là hai tiến trình `gather` và `quan` dùng cùng file kho theo mục G. | Đối chiếu PRD-0 và live adapter đã tích hợp |
| P1-02 | 2026-11-21 | Nếu fixture rút ngắn ca hoặc khách hết kiên nhẫn đúng tick đóng ca thì xử lý thế nào? | `phase_tick` vẫn tính từ 0. Xét phục vụ trước, sau đó khách còn chờ rời với `closing` và giữ nguyên uy tín. Dọn món thuộc đơn đã rời, giữ phần nguyên liệu đã tiêu. | PRD-0 mục D và F |
| P1-03 | 2026-11-21 | Hồ sơ bàn giao dùng mã nhóm và dữ liệu kho nào? | Mã nhóm `nhom-ba-khi`, `team_size` là 4. Schema kho v1.0 và tuning dùng preset hiện có. Kiểm giữ chỗ theo `quan.stock` hoặc kho nạp từ `--inventory`. | Quy ước nhóm và PRD-0 mục A, D, G |
