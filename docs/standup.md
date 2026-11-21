# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | `nlamtung` (TV1) | Điền `TEAM.md`, `game.contract.json`, chốt `docs/contracts/README.md`, hoàn thiện `sim/gather` (Lát 1–2) & `test_gather_p1.py` | Rà soát DoD Phase 1, sửa link verification, cập nhật `README.md` và gắn tag `phase-1` | Không |
| 1 | `Tiberu2611` (TV2) | Đối chiếu PRD-0, ghi `docs/clarify.md`, `docs/plan/phase-1.md`, hoàn thiện `sim/quan` Lát 3 & validation mã `2` trong `scenario.py` | Hỗ trợ rà soát tích hợp với Lát 4 và chuẩn bị Phase 2 | Ban đầu code trước khi có PRD-0 nên phải sửa lại 9 mục theo PRD-0 |
| 1 | `khanhduyvu1` (TV3) | Hoàn thiện `sim/quan` Lát 4 (bếp, bưng, phục vụ, tiền/boa/uy tín) và test tích hợp 2 tiến trình `gather` → `quan` | Bổ sung log AI cá nhân & chuẩn bị Phase 2 | Cần khớp cấu trúc `stoves[].dish` và `hand` với Lát 3 (đã giải quyết) |
| 1 | `Presceltooo` (TV4) | Nâng cấp `chonoi/web/index.html` (Canvas 2D, hiệu ứng hạt sóng/bọt/khói, âm thanh Web Audio API) | Bổ sung log AI cá nhân & nâng cấp thêm đồ họa miền Tây ở phase sau | Lỗi hiển thị `st.dish` dạng object (đã sửa) |
| 1 | `nguyenduong43` (TV5) | Viết 2 skills (`verify-contract`, `qa-blackbox-check`), cập nhật `AGENTS.md`, viết `test_qa_regression_p1.py`, xuất bằng chứng `docs/proof/phase-1/` & `docs/verification/phase-1.md` | Theo dõi regression & đổi tên file phản tư cá nhân theo `<handle>.md` | `test_live.py` bị chặn socket trong sandbox (đã xử lý skip có điều kiện) |
