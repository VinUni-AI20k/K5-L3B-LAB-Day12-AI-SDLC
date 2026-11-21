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

## Sau Release — Duyet (Claude Code · Claude Opus 5.5) — 2 skill + cập nhật AGENTS.md
- Việc: viết `.agents/skills/pre-push-check/` (SKILL.md + `check.py`) và `.agents/skills/verify-tag/` (SKILL.md + `verify_tag.py`); cập nhật AGENTS.md (lệnh Phase 3/4: soak, bench, proof, GUI chạy từ gốc repo; quy tắc "xong" và sở hữu file rút từ retro; mục Skills). Trước đó đổi màu tim Máu ở client (`39fc18e`).
- Kiểm: `check.py` → contract v1.3 OK, unittest 162 OK, headless gather/quan/day exit 0 (1 Ngày 1.0 s ≤ 20 s), 28 file JS không lỗi cú pháp, `check_team` WARN (handle Duyet/Nhat Minh chưa điền, 3 người < 4). Thử đường lỗi (JS sai cú pháp, thiếu `chonoi`) → FAIL đúng. Lệnh soak trong AGENTS.md chạy thật 10/10; bench chưa chạy được trên máy này (không có Chrome).
- AI sai: script kiểm đầu tiên treo vì để stderr của `http.server` vào pipe không đọc; bước `team` ra thông báo rỗng vì `check_team.py` in lỗi ra stderr; tham số mặc định `cwd=ROOT` bị chốt lúc định nghĩa; lỗi node lấy nhầm dòng phiên bản thay vì dòng `SyntaxError`. Đều phát hiện khi chạy thử và đã sửa.

## Sau Release — Nhat Minh (Claude Code · Claude Opus 5.5) — test shop/ramp, ADR-0001, màu tương phản cao
- Việc: unit test `chonoi/sim/shop.py` + `ramp.py` (`tests/test_shop_ramp_units.py`, 8 test); thay `TODO(nhóm)` đã làm trong docstring `chonoi/scenario.py` bằng chỗ kiểm thật ở `sim/quan.py`; ADR-0001 (RNG tách luồng + số liệu từ contract); ở quán: vòng kiên nhẫn và thanh chờ bàn dùng chung thang xanh lá → vàng → đỏ và bảng màu `a11y.HC` khi bật tương phản cao; `freshColor` có kiểu tương phản cao (món ươn xám sáng `#c8c8c8`).
- Kiểm: `pre-push-check` → unittest 170 OK, headless gather/quan/day exit 0 (1 Ngày 0.4 s), client-js SKIP (máy không có node). Chơi thử bản demo "Buổi tối — Quán" trên trình duyệt (`?debug`): console không lỗi; đặt tạm kiên nhẫn 3 khách 0.9/0.45/0.15 và đếm điểm ảnh canvas `px` → thường xanh/vàng `#ffd23a`/đỏ `#ff3a3a`, tương phản cao `#ffef00`/`#ff2a2a`. `freshColor` gọi thử đúng cả hai chế độ. Thanh chờ bàn chưa thấy trên màn hình (cần đủ bàn kín khách), chỉ kiểm qua code.
- AI sai: bản nháp ADR ghi `recoil_dir` là một luồng RNG, thực ra là trường dữ liệu của thủy quái; phát hiện khi grep `get("…")` trong `chonoi/sim` và đã sửa trước khi commit. Lần sửa câu ví dụ đầu tiên để thừa một vế lặp, đọc lại thì thấy và sửa.

## Cao Duy Minh (`workcaominh-gif`) — báo cáo cuối
- Nhờ Claude Code soạn nháp phần đóng góp của mình trong `docs/retro.md` (mục "Đóng góp từng người") và phản tư `docs/members/workcaominh-gif.md`, dựa trên `git log`, tag và báo cáo các phase. Đã đọc lại, sửa cho đúng việc mình làm; chỉ điền dòng của mình, không viết hộ thành viên khác.

## Sau Release — Claude Code · Claude Opus 5.5 — Mở rộng: bảng xếp hạng + phụ đề SFX
- Việc: `chonoi/leaderboard.py`; cờ `--leaderboard/--player-name` ở `chonoi/headless.py`; `--export-leaderboard` ở `chonoi/live.py` (file khung — ghi trong CHANGELOG); `tests/test_leaderboard_p4.py` (17 test); client `captions.js` (phím U, tự bật khi tắt tiếng, phụ đề theo ngữ cảnh ở lặn/quán), `leaderboard.js` + nhập tên/top 10 ở `Summary`; script `docs/proof/phase-4/ext/ui_check.mjs` điều khiển Chrome headless qua CDP.
- Kiểm: `pre-push-check` → unittest 187 OK, headless exit 0, 31 file JS OK; `ui_check.mjs` → không lỗi console, đủ trạng thái kỳ vọng (xem `docs/verification/phase-4.md` AC-P4-X01..X09).
- AI sai: (1) bản đầu nhập tên ở màn tổng kết để phím H/T vẫn chạy như phím tắt → gõ "Tester" sẽ bật tương phản cao và mở điện thoại; phát hiện khi đọc lại vòng `frame()` trong `main.js`, thêm cờ `scene.typing` rồi kiểm lại bằng `ui_check.mjs` (`chonoi.hc` không đổi, `overlay:false`). (2) Lệnh `pkill -f "http.server 8099"` tự khớp với chính shell đang chạy nó nên giết luôn lệnh sau; chạy lại không dùng pkill. (3) Test đầu tiên để mở file không đóng (ResourceWarning) — sửa bằng helper `_text`.
- Người thực hiện: `Sz3RO` (thêm vào `TEAM.md` ở commit `docs(team)` ngay sau).
