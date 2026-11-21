# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | B (`LaanLee`) | Lát 2 gather: hái nút, bắt cá, `hold_full`, kho cuối buổi (`_try_harvest`, `_try_catch`), 32 test `tests/test_gather_lat2.py`, file kho thật + smoke 2 tiến trình trong `docs/proof/phase-1/`, điền `TEAM.md` và `team_size: 5` | Mở PR Lát 2 cho A đọc diff; chờ PO trả lời 3 câu Lát 2 trong `docs/clarify.md` (#4–#6); chuyển sang Phase 2 | Windows không có `python3` thật (phải dựng venv); 3 giả định Lát 2 chưa được PO xác nhận |
| 1 | E (`common-maker`) | HUD 2 buổi pixel art + animation mượt & sprite cá (`assets/fish/`), 2 skill (`smoke-p1`, `verify-ac`), `docs/plan/phase-1.md`, `tests/test_e_qa_p1.py`, smoke 2 tiến trình + `docs/proof/phase-1/`, `README.md`, `CREDITS.md`, `docs/verification/phase-1.md`, `docs/members/common-maker.md` | Mở PR nhánh E vào `main`; chạy lại `verify-ac` lần cuối khi `TEAM.md` đủ 5 người trước khi A gắn tag `phase-1` | `TEAM.md` trên `main` chưa có 5 thành viên (`check_team.py` thoát mã 1) và `CREDITS.md` chờ nguồn ảnh `assets/fish/` |
