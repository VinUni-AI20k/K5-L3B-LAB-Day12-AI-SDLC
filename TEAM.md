# TEAM

**Tên nhóm:** nhom6ae  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Ngô Chí Vĩnh (2A202603724) | NgChiVinh | `sim/gather` lát 1: bơi, oxy, ngạt, Máu, giỏ · `docs/contracts/` · AGENTS.md + skills | Integrator (chốt hợp đồng kho/sự kiện, tích hợp, gắn tag) | TrungHieuPh |
| Phan Trung Hiếu (2A202603763) | TrungHieuPh | `sim/gather` lát 2: hái, bắt cá, cập bến, ghi file kho | PO (hỏi Anh Năm hàng xóm, giữ `docs/clarify.md`) | NgChiVinh |
| Lê Đức Trúc Lâm (2A202603787) | truclamld | `client/ui`: HUD hai buổi (`chonoi/web/`, `live.py`) · README (chạy, điều khiển, điểm) | Scrum/Release (theo dõi mốc, standup) | HoangQuan23112004 (từ phút 20) |
| Lê Viết Khoa (2A202603737) | khoa-asta | `qa`: test hộp đen theo AC, smoke hai tiến trình, `docs/verification/` + `docs/proof/` | QA lead | truclamld |
| Hoàng Dương Anh Quân (2A202603735) | HoangQuan23112004 | `sim/quan` lát 4: bếp, bưng, phục vụ, tiền, boa, uy tín, đóng ca | — | 22520160 |
| Phạm Lê Chuẩn (2A202603784) | 22520160 | `sim/quan` lát 3: khách, giữ chỗ, kiên nhẫn, rời bàn · kiểm scenario quán (`scenario.py`) | — | HoangQuan23112004 |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: nhóm chat của nhóm + nói trực tiếp tại lab.
- Khi bất đồng về thiết kế: mỗi bên nói 2 phút, không xong thì Integrator quyết và ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng (cột cuối) vào giúp hoặc nhận việc.
- Giờ standup giữa phase: giữa mỗi phase, mỗi người 1 dòng trong `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát của người dự phòng mình trước khi gộp; QA lead chạy test hộp đen.
- Cách làm việc với Git: nhánh ngắn theo lát rồi gộp vào `main` (pull --rebase, chạy test trước khi push); chỉ Integrator gắn tag `phase-n`.

> **Mỗi người (Phase 4):** viết `docs/members/<handle>.md` (≤ 200 từ, có link commit) và 1 dòng `docs/ai-usage-log.md`.

## Việc theo phase (chi tiết, phụ thuộc, AC: `docs/plan/phase-n.md`; đề: `docs/prd/phase-n.md`)

| Thành viên | Phase 1 ([plan](docs/plan/phase-1.md)) | Phase 2 ([plan](docs/plan/phase-2.md) · [đề](docs/prd/phase-2.md)) | Phase 3 — làm trên nhánh `v1.2`, KHÔNG push `main` ([ADR](docs/adr/0001-kho-ca-the-do-tuoi.md) · [đề](docs/prd/phase-3.md)) | Phase 4 — nhánh ngắn → PR vào `main` ([plan](docs/plan/phase-4.md) · [đề](docs/prd/phase-4.md)) |
|---|---|---|---|---|
| NgChiVinh | Lát 1 gather, hợp đồng, harness, tích hợp | **#0 khung v1.1 (push trước)** + **#4 `--mode day` + pause**, tích hợp, tag | ĐÃ XONG lõi v1.2 trên nhánh `v1.2` (adapter `items.py`/`inventory.py`, contract, scenario, giỏ, kho quán, giữ chỗ theo id, giá theo tươi, Shop, day, `tests/helpers.py`). Còn: tích hợp `v1.2` → `main` qua PR, CHANGELOG, bằng chứng trên đúng commit, tag `phase-3` | Release/Integrator: contract v1.3 (`bench_cmd`, `soak_cmd`), bench có render (`chonoi/bench.py`), release notes, CHANGELOG, tag `phase-4` + Release v1.0.0 |
| TrungHieuPh | Lát 2 gather, PO | **#1 số chuẩn gather + cá bơi/sinh**, PO (hỏi Anh Năm) | Sửa test giỏ theo v1.2: `test_gather_lat1`, `test_gather_lat2`, `test_qa_phase2` (hold/lost/inventory là mảng cá thể — dùng `kinds_of()`, `counts()`); kiểm hái/bắt tạo cá thể fresh 100 | Soak: `chonoi/soak.py` 10 Ngày, kế hoạch D1–D5 lặp Ngày 6–10, bot tất định, `soak.json` |
| 22520160 | Lát 3 khách + kiểm scenario quán | **#2 Cá Sấu, `monster_hit`, ngất do quái** (`chonoi/sim/monsters.py`) | Sửa `test_gather_monsters` (`lost` cá thể), `test_quan_lat3` (unit: stock là mảng cá thể); kiểm giữ chỗ theo id + ươn → nhả và giữ lại 1 lần | Mở rộng 2 — Bảng xếp hạng (`leaderboard`): top 10 bền vững, cờ `--leaderboard --player-name`, `--export-leaderboard`, test |
| HoangQuan23112004 | Lát 4 bếp, phục vụ, tiền | **#3 2 bếp/4 bàn/6 món, lọc menu theo kế hoạch + Shop** (`chonoi/sim/shop.py`) | Sửa `test_quan_lat4`, `test_p2_quan_shop` (giá = floor(niêm yết × fresh TB / 100), `cook_started.items` mảng cá thể, stock mảng cá thể) | Đóng gói: clone sạch ≤ 3 lệnh, README (môi trường, điều khiển, test, headless, bench), gói Release, CREDITS/LICENSE; Mở rộng 1 — bật Cháy món (`burn`) |
| truclamld | HUD, README, Scrum | **#5 menu, các màn hình ngày, pause, HUD v1.1**, retro nhanh | HUD độ tươi / nhãn ươn cho giỏ và kho (stock giờ là mảng cá thể — HUD hiện tại hiển thị sai), cập nhật `hud_check` | 3 cảnh báo (thủy quái gần, oxy sắp hết, khách sắp giận) + chế độ tương phản cao, chơi thử; điều phối retro cuối |
| khoa-asta | QA, verification | **#6 regression P1 số chuẩn, smoke phút 20, smoke day, verification P2** | Test v1.2 mới (`tests/test_qa_phase3.py`: ngưỡng fresh 30 → spoiled tick 1, giữ lại khi vừa ươn, chốt giá, bàn giao file + day), sửa `test_smoke_p1`/`test_python_starter_units`, `docs/proof/phase-3/`, `docs/verification/phase-3.md` | Bench/QA: chạy bench + soak + regression + smoke trên commit bàn giao, `docs/proof/phase-4/`, `docs/verification/phase-4.md` |
