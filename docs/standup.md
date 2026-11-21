# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | `nlamtung` (TV1) | Điền `TEAM.md`, `game.contract.json`, chốt `docs/contracts/README.md`, hoàn thiện `sim/gather` (Lát 1–2) & `test_gather_p1.py` | Rà soát DoD Phase 1, sửa link verification, cập nhật `README.md` và gắn tag `phase-1` | Không |
| 1 | `khanhduyvu1` (TV2) | Đối chiếu PRD-0, ghi `docs/clarify.md`, `docs/plan/phase-1.md`, hoàn thiện `sim/quan` Lát 3 & validation mã `2` trong `scenario.py` | Chuẩn bị Change Request Phase 3 (kho cá thể & độ tươi v1.2) | Ban đầu code trước khi có PRD-0 nên phải sửa lại 9 mục theo PRD-0 |
| 1 | `Tiberu2611` (TV3) | Hoàn thiện `sim/quan` Lát 4 (bếp, bưng, phục vụ, tiền/boa/uy tín), test tích hợp `gather` → `quan`, test bất biến & test chờ P2/P3 | Triển khai `sim/quan` v1.1 (2 bếp, 4 bàn, 6 món, `burn`) & `--mode day` (Shop/Pause) | Cần khớp cấu trúc `stoves[].dish` và `hand` với Lát 3 (đã giải quyết) |
| 1 | `Presceltooo` (TV4) | Nâng cấp `chonoi/web/index.html` (Canvas 2D, hiệu ứng hạt sóng/bọt/khói, âm thanh Web Audio API) | Nâng cấp UI/HUD cho vòng ngày, độ tươi, 3 cảnh báo + chế độ tương phản cao (P2–P4) | Lỗi hiển thị `st.dish` dạng object (đã sửa) |
| 1 | `nguyenduong43` (TV5) | Viết 2 skills (`verify-contract`, `qa-blackbox-check`), cập nhật `AGENTS.md`, viết `test_qa_regression_p1.py`, xuất bằng chứng `docs/proof/phase-1/` & `docs/verification/phase-1.md` | Viết `bench_cmd`, `soak_cmd` và chạy verification cho Phase 2–4 | `test_live.py` bị chặn socket trong sandbox (đã xử lý skip có điều kiện) |
