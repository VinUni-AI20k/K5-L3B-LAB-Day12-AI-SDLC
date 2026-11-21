# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | `client/ui` | Codex | Triển khai menu, HUD, Canvas, live adapter và snapshot mẫu. Chạy Chrome headless và suite Python. | — | Checkout còn TODO ở hai sim. Kiểm tra thu hoạch và chu trình phục vụ bằng snapshot mẫu, bàn giao kho bằng mô phỏng thật. |
| Phase 1 | Nguyễn Văn Lâm | Antigravity (Gemini 3.8 Flash) | Cài đặt toàn bộ Lát 3 & 4 (sim/quan), bổ sung fixture check và suite test_quan.py | ~45k tokens | Ban đầu tạo InputState trực tiếp thiếu tham số positional; đã sửa bằng helper tạo InputState chuẩn theo khung inputs.py |
| Phase 1 | Đặng Nguyễn Nhật Minh (`MN-HD`) | ChatGPT Work (Codex) | Hỗ trợ thiết kế hai ca kiểm thử hộp đen, phân tích lỗi ngất ở tick biên và soạn bằng chứng QA. | Không đo | Hướng dẫn ban đầu dự kiến đưa ma trận vào PR #3, nhưng PR đã merge trước khi commit ma trận được đẩy. Kiểm tra trên GitHub và mở PR #5 để bổ sung. |
| Phase 2 | Nguyễn Văn Lâm (`lam2121`) | Antigravity (Gemini 3.8 Flash) | Cập nhật contract v1.1, triển khai QuanSim Phase 2 (2 bếp, 4 bàn, 6 món, day_plan, tip floor, closing, burn), viết suite 11 test | ~55k tokens | AI ban đầu dùng round() cho boa thay vì floor(); đã đọc lại TICKET-02 và chỉnh về math.floor(). Khi chạy live test trên Windows, cổng 8000 bị Docker chiếm dụng nên chuyển sang cổng 8080. |

