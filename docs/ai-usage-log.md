# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Nguyễn Tiến Đạt (`duhocsinh4to10`) | Antigravity (Gemini) | Đọc dự án, thiết kế & nâng cấp `chonoi/web/index.html` (HUD `gather`/`quan`, hỗ trợ `--extra-content` & sprite atlas), viết `tests/test_ui_live.py` và kiểm chứng render trên Node + `unittest`. | ~40k token | Lần chạy đầu gặp `WinError 1920` do Windows Store alias `python3` đứng trước Python 3.13 trong `PATH` và lệch merge khi kéo `7a5d7df` (`--extra-content`); đã phát hiện qua `git fetch`/`git show` trước khi merge để giữ đủ cả hai thay đổi. |
