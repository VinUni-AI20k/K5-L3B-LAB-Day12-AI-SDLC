# khoa-asta — phản tư cá nhân

- Tôi đã làm: chạy bench đúng cấu hình 30 giây, soak 10/10 ngày không crash và tất định, regression 127/127, smoke gather → quan 7/7; lưu bằng chứng trong [commit QA](https://github.com/NgChiVinh/K5-L3B-LAB-Day12-AI-SDLC-nhom6ae/commit/5599f64).
- Tôi đã review: đối chiếu lệnh bench với contract và kiểm tra đầu ra render trên [commit được kiểm chứng](https://github.com/NgChiVinh/K5-L3B-LAB-Day12-AI-SDLC-nhom6ae/commit/1df38e5737f3f0f9ef346225ae41d3a35dfe6626).
- AI sai ở đâu và tôi phát hiện thế nào: snapshot ban đầu thiếu tài liệu Phase 4; kiểm tra sau `git pull` cho thấy chúng đã có trên `main`. Smoke lần đầu lỗi do stdout cp1252 trên Windows, không phải lỗi game; chạy lại với UTF-8 và đạt 7/7.
- Điều tôi học được: phải cập nhật nhánh theo `main` trước khi kết luận về blocker; PR #15 đã tích hợp soak, sau đó tôi chạy lại và xác nhận đủ 10 ngày, 0 crash.
