# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Khôi | Codex | Đối chiếu PRD-0 với starter, gợi ý phân công và soạn nháp hợp đồng tích hợp | Chưa đo |  |
| 1 | Khôi | Codex | Hỗ trợ triển khai HUD hai ca, viết hướng dẫn chạy và kiểm với snapshot mẫu | Chưa đo | Bản HUD ban đầu hiện `NaN:NaN` khi snapshot thiếu bộ đếm kiên nhẫn. Đã sửa để hiện `đang chờ` và kiểm lại 5 tình huống. |
| 1 | Khôi | Codex | Hỗ trợ chạy hồi quy, smoke bàn giao kho và kiểm HUD bằng Chrome headless trên `b772097` | Chưa đo ||
| 1 | Diên | Claude Code (Claude Opus 5.5) | Đối chiếu PRD-0 mục D–G với starter, viết luật Lặn & Hái (oxy, ngạt, hái, bắt cá, ngất, bàn giao kho) và 27 test hộp đen, kiểm test bằng 17 bản cài lỗi cố ý | Chưa đo | AI chạy smoke từ `tmp/` nên thoát mã 1. AI gợi ý dán khối lệnh mở đầu bằng `git diff`, pager nuốt các lệnh sau nên không có commit. Phát hiện qua mã thoát và `git log`, đổi sang chạy từ gốc repo, `git --no-pager` và `git commit -F`. |
| 2 | Khôi | Codex | Trích số liệu Ticket-02, lập tiêu chí chấp nhận và soạn nháp giao diện Gather, Quán, Shop | Chưa đo |  |
| 2 | Khôi | Codex | Hỗ trợ triển khai vòng ngày, Shop, pause, CLI và giao diện trình duyệt | Chưa đo | |
| 2 | Khôi | Codex | Hỗ trợ bật v1.1, cập nhật hồi quy và chạy smoke | Chưa đo |  |
| 2 | Diên | Claude Code (Claude Opus 5.5) | Cá bơi và sinh theo seed, Cá Sấu (patrol, chase, hit, recoil, ngất), 22 test mức sim với tuning Ticket-02, kiểm bằng 30 bản cài lỗi | Chưa đo | Helper test vẫn gọi `step()` sau khi ca kết thúc. Tọa độ Cá Sấu bị chặn thành số nguyên, làm đổi kiểu số trong JSONL. Test sinh cá đầu tiên quá lỏng. Phát hiện khi rà code và chạy bản cài lỗi, đã sửa trước khi commit. |
| 3 | Khôi | Codex | Đối chiếu Ticket-03, chuẩn bị fixture, soạn nháp ADR và phân công cho ba PR | Chưa đo |  |
| 3 | Khôi | Codex | Hỗ trợ nối adapter của Diên, Quán của Nhân và bổ sung giỏ cá thể Gather, CLI, Day/Shop và HUD | Chưa đo ||
| 3 | Diên | Claude Code (Claude Opus 5.5) | Adapter kho cá thể `chonoi/freshness.py` và đọc/ghi kho theo version, 10 test, kiểm bằng 11 bản cài lỗi, tối ưu `age_items` từ 18.4 xuống 12.4 µs/tick | Chưa đo | Test ban đầu không bắt được lỗi đọc số qua float. Một bản cài lỗi bị dựng sai thành lỗi cú pháp. Phát hiện khi đối chiếu hợp đồng và đọc kết quả, đã sửa. |
