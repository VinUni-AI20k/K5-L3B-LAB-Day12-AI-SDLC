# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | E | Antigravity (Orchestrator / Gemini) | Nâng cấp HUD 2 buổi (`chonoi/web/index.html`) & hiển thị sprite `assets/fish/`, viết 2 skill (`smoke-p1`, `verify-ac`), lập `docs/plan/phase-1.md`, viết `tests/test_e_qa_p1.py`, chạy smoke 2 tiến trình + lưu `docs/proof/phase-1/`, điền `docs/verification/phase-1.md`, cập nhật `README.md` & `CREDITS.md` | ước tính ~70k–90k token (phiên nhiều lượt) | Lần đầu tìm thư mục `fish/` bị nhầm nằm trong `chonoi/web/` thay vì gốc repo (đã chuẩn hóa vào `assets/fish/` và kiểm bằng test); có thêm route `/assets/` vào `chonoi/live.py` (file nhạy cảm, cần báo Integrator A trước khi merge); phát hiện và sửa lỗi starter `index.html` in `[object Object]` cho `st.dish` và thiếu tính kho khả dụng |
