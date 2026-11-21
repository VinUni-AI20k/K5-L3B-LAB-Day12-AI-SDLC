# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Tào Quang Vinh | Hoàn thành HUD 2 buổi sáng/tối (Ticket 06), prompt ngữ cảnh, overlay kết thúc, kịch bản demo | Hỗ trợ review PR của Văn Minh, chuẩn bị UX/SFX Phase 2 | Không vướng |
| Phase 2 | Tào Quang Vinh | Tích hợp hệ thống âm thanh procedural Web Audio (0 KB), hiệu ứng bọt khí/khói bếp, hoàn thiện proof HUD | Sẵn sàng review PR cho Văn Minh, đồng bộ các tính năng mở rộng tiếp theo | Không vướng |
| Phase 3 | Tào Quang Vinh | Hoàn thành HUD độ tươi & hàng ươn (Ticket 05 P3), cờ ?fx=0, toast thông báo spoiled | Sẵn sàng demo, đóng gói Phase 4 và retro | Không vướng |
| Phase 4 | Tào Quang Vinh | Hoàn thành Ticket 03 P4: 3 cảnh báo nguy hiểm chữ + icon (Thủy quái, Hết hơi, Khách giận), chế độ tương phản cao (phím C, ?hc=1) | Chuẩn bị tài liệu demo tổng kết và đóng gói dự án | Không vướng |
| 1 | Nhật Minh | Lát 2 + 25 test CLI, nối core Cao Minh trên `feat/nhat-minh`; 62/62 test qua ở bản làm việc | Cao Minh review; xác nhận Q1 với trợ giảng | Q1 vẫn là giả định; chưa có review của người |
| 2 | Nhật Minh | Cài cá bơi/sinh và vợt; test CLI cá + test CLI vợt với patch bàn giao trong thư mục tạm | Review phần `fish.py`, catch và hooks; Integrator ghép contract/day/shop | Nhánh cá nhân vẫn dùng contract v1.0; không sửa file của owner contract |
| 3 | Nhật Minh | Cài hao tươi, spoiled, item IDs/LIFO và dòng nước; kiểm component, Cá Sấu và lịch current qua CLI có hooks | Ghép với Stock, validator v1.2 và vòng day khi owner bàn giao | Chưa có adapter Stock trong dependency đã đọc; chưa xác nhận migration/kho file v1.2 |
| Phase 1 | Phạm Hoàng Đức Minh | Hoàn thành Lát 4 Quán service (Ticket 05 P1): nấu bếp, ready_ticks, bốc món, phục vụ, boa, tính tiền, đóng ca; 14 test xanh | Review PR Cao Minh (PR #1), chuẩn bị Phase 2 | Không vướng |
| Phase 2 | Phạm Hoàng Đức Minh | Hoàn thành Ticket 04 Phase 2: Quán 2 bếp B1/B2 nấu song song, 4 bàn T1-T4, 6 món với 2 nguyên liệu mới (ca_keo, keo_neo), lọc món theo day_plan; 6 test xanh | Review PR Cao Minh (Ticket 05 P2), điều phối cổng kiểm trước tag phase-2 | Không vướng |
