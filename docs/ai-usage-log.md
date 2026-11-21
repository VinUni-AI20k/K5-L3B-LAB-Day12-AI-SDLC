# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Minh (Claude Code session) | Claude Code · Claude Opus 5.5 | Chép Test Contract v1.0 từ lab board vào `docs/contracts/test-contract-v1.md`; viết luật `gather` (lát 1–2) + `quan` (lát 3–4), 35 test mới, bot tạo inputs lượt đầy đủ, proof, ma trận truy vết | không đo được | Lab board không xuất được text (iframe) → chép từ ảnh chụp, vài dòng cuối bị cắt (đã ghi "không đọc được"). Cần người đọc lại lát 3–4 trước khi Duyet commit. |
| 2 | Minh (Claude Code, agent A) | Claude Code · Claude Opus 5.5 | Dữ liệu contract v1.1, `contract.py`, `inventory.py` (6 loại), `gather.py` (cá bơi/sinh, Cá Sấu, Máu/ngất, tham số Ngày/nâng cấp), `tests/test_gather_p2.py` (AC-P2-01..29), viết lại AC-P1-18 | không đo được | Nhiều chỗ ticket không chốt (thứ tự RNG, phản xạ, recoil) → ghi giả định C-P2-A01..A10, cần người đọc lại trước khi tag. |
| 2 | Minh (Claude Code, agent B) | Claude Code · Claude Opus 5.5 | `quan.py` (lọc kế hoạch, mang tiền/uy tín), `sim/day.py`, `sim/shop.py`, pause ở `runner.py`, `inputs.py` (pause/shop_done/buy), `scenario.py` (khối day), `headless.py` (`--days`), 31 test P2 (quán/day/shop/pause/smoke), sửa 4 test P1 có lý do, proof + ma trận + plan | không đo được | Lần đầu script proof chọn nhầm snapshot Shop (snapshot-every 600 không có snapshot sau khi mua) → assert hỏng, sửa sang đối chiếu event `bought`. UI (menu/HUD/pause trong trình duyệt) AI chưa làm. |

## Phase 3 — Agent F (Claude) — Quán/day/Shop v1.2
- Việc: chuyển `quan.py` sang kho cá thể + hao tươi + giữ theo id + giá chốt; `day.py`/`shop.py`/`scenario.py`/`headless.py` theo schema mới; lớp chuyển fixture `tests/v12_compat.py`; test `test_quan_p3.py`, `test_smoke_p3.py`; proof + docs Phase 3.
- Kiểm: full test 151 OK; `docs/proof/phase-3/run_proof.sh`. Người cần đọc lại trước commit (chưa commit).

## Phase 4 — Agent (Claude Code · Claude Opus 5.5) — Bench + Soak v1.3
- Việc: contract 1.3 + `validate_root`; `DaySim.plan_for` (lặp kế hoạch); `tools/soak.py` (bot tham lam), `tools/bench.py` + `client/bench.html` + `client/src/bench.js`; `tests/test_p4_soak.py` (11 test); proof `docs/proof/phase-4/`; `docs/verification/phase-4.md`.
- Kiểm: 162 test OK; bench 30 s thật trên Chrome headless; soak 10/10.
- AI sai/thiếu: 3 test cũ khóa cứng `contract_version == "1.2"` → nới thành chấp nhận "1.2"/"1.3" (có lý do: ticket đổi version). Bot chưa đủ nguyên liệu ở Ngày 4/8/10 (earned không tăng). Lần đo thử đầu `load_ms` 9909 ms (Chrome lạnh) — cần đo lại trên máy chấm. Người cần đọc lại trước commit (chưa commit).
