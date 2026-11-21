# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 (cập nhật công việc 21/11/2026, không ghi nhận cuộc họp thực tế) | `chur04` | Lát 4 + 28 test + bằng chứng; clarify đã đối chiếu PRD | Bàn giao Nhung tích hợp lịch khách, QA review trên main | Lát 3 chưa có lịch sinh khách/validation schema đầy đủ; tránh giảm timer/dọn đơn hai lần; chưa commit/push/tag mới |
| Phase 1 | Nguyễn Tiến Đạt (`duhocsinh4to10`) | Nâng cấp đầy đủ HUD & đồ họa `chonoi/web/index.html` cho `gather` và `quan`; tích hợp `--extra-content`, sprite atlas & animation bơi `ut-sen-swim.png`, và tương thích `quan_service.py` (`order_id`); viết `tests/test_ui_live.py` và bằng chứng `docs/proof/phase-1/ui-live-check.md`. | Đồng bộ `origin/main` vào `duhocsinh`, kiểm thử toàn bộ suite sau tích hợp và hỗ trợ demo cuối phase. | Không vướng; trên Windows cần chạy Python 3.13 trực tiếp thay vì alias WindowsApps `python3`. |
