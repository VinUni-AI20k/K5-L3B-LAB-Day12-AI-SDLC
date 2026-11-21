# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | `capkhai` | Chốt kickoff (`TEAM.md`, kế hoạch, hợp đồng), cài đủ Lát 1 & Lát 2 `chonoi/sim/gather.py` khớp PRD-0 + `tests/test_gather.py`, giải quyết conflict gộp `nhungvo` & `duhocsinh` lên `main`. | Chốt bằng chứng tổng hợp + tag `phase-1`, triển khai tiếp Phase 2 (cá bơi/sinh). | Nhánh `nhungvo` ban đầu lệch schema với `chur04`, đã đồng bộ xong và pass toàn bộ test. |
| 1 (cập nhật công việc 21/11/2026, không ghi nhận cuộc họp thực tế) | `chur04` | Lát 4 + 28 test + bằng chứng; clarify đã đối chiếu PRD | Bàn giao Nhung tích hợp lịch khách, QA review trên main | Lát 3 chưa có lịch sinh khách/validation schema đầy đủ; tránh giảm timer/dọn đơn hai lần; chưa commit/push/tag mới |
| 1 | Nguyễn Tiến Đạt (`duhocsinh4to10`) | Nâng cấp đầy đủ HUD & đồ họa `chonoi/web/index.html` cho `gather` và `quan`; hợp nhất hỗ trợ `--extra-content` & sprite atlas từ `7a5d7df`; viết `tests/test_ui_live.py` và bằng chứng `docs/proof/phase-1/ui-live-check.md` (36/36 test pass). | Commit/push nhánh UI, chơi thử tích hợp khi Người 1–3 gộp luật `gather`/`quan` và hỗ trợ demo cuối phase. | Không vướng; trên Windows cần chạy Python 3.13 trực tiếp thay vì alias WindowsApps `python3`. |
