# linkiewinkie — phản tư cá nhân

> Bản nháp Phase 1 để Nguyễn Xuân Khánh Linh xác nhận và bổ sung cuối buổi.

- Tôi phụ trách docs và harness AI. Tôi dùng Codex để soạn kế hoạch, cập nhật TEAM và ghi câu hỏi cho PO. [Commit kế hoạch](https://github.com/justapea25/K5-L3B-LAB-Day12-AI-SDLC-MATH/commit/482db277c7b9a666f7239108d32168068ebb7dc5)
- Tôi chuẩn bị ma trận kiểm chứng và hai lệnh lưu log. Kết quả trên mã tại `c872ef2` là 41 test qua và JSONL khớp từng byte khi chạy lại cùng seed cho cả hai mode. [Commit bằng chứng](https://github.com/justapea25/K5-L3B-LAB-Day12-AI-SDLC-MATH/commit/5a1dc6c8a13f997ce69966d9ceda9098f30d3ff5), [ma trận](../verification/phase-1.md)
- Review của tôi còn chờ bổ sung đường dẫn PR.
- Bản lệnh AI soạn ban đầu gây lỗi giải mã stderr dù unittest báo OK. Log đầy đủ cho thấy lỗi ở tiến trình con. Bật UTF-8 cho tiến trình test và chạy lại cho log sạch.
- Một điều rút ra từ lượt này là cần ghi commit, đầu vào và phần hành vi đã chạy để người khác lặp lại được kết quả.
