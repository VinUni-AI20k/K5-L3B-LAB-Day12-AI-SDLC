# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Vũ Huy Hiệu (`hieunhangia`) | Gemini 3.8 Flash (High) | Khởi tạo TEAM.md 6 người, cập nhật contract team_size, chốt hợp đồng tích hợp docs/contracts, thiết lập AI skills & quy tắc AGENTS.md | ~25,000 tokens | AI ban đầu tự động gợi ý các SOP cồng kềnh ngoài luồng; đã yêu cầu gác lại để bám sát Test Contract của giảng viên. |
| Phase 1 | Nguyễn Huy Tấn (`Besoi2004`) | Claude Code / Claude Opus 5.5 | Lát 2: viết `_harvest`, `_catch`, `_nearest` trong `gather.py`; 8 test `tests/test_gather_items.py`; chạy smoke và lưu proof | không đo được | Kế hoạch `task.md` ghi `hold_full` khi `len(hold) >= capacity` và vẫn đặt hồi chiêu khi giỏ đầy, sai PRD-0 (phải là `free < yield`, không đặt hồi chiêu); đã sửa theo PRD và kiểm bằng test. |
