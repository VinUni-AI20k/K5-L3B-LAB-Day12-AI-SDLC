# TEAM

**Tên nhóm:** T77  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| (A — điền tên) | (điền handle) | `sim/gather` (lát 1 + 2) | PO | B |
| (B — điền tên) | (điền handle) | `sim/quan` (lát 3 + 4) | Scrum | A |
| Ngoc Hung | Ngochung1772k4 | `client/ui` + `docs/contracts` + `scenario` | Integrator | D |
| (D — điền tên) | (điền handle) | `qa` + harness AI | QA lead / Release | C |

**Vai quy trình:** PO (đầu mối hỏi Anh Năm / giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, merge vào `main`, gắn tag) · QA lead (bộ test, ma trận truy vết) · Scrum/Release (standup, mốc bàn giao).

Chi tiết việc từng người: [docs/plan/phase-1-chia-viec.md](docs/plan/phase-1-chia-viec.md).

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: nhóm chat chung của T77; việc gấp thì nói trực tiếp.
- Khi bất đồng về thiết kế: mỗi bên trình bày 2 phút; chưa xong thì Integrator (C) quyết, ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh; người dự phòng (cột cuối) nhận hỗ trợ hoặc pair.
- Giờ standup giữa phase: phút 20 và phút 35 của mỗi phase, 2–3 phút (đã xong / sắp làm / vướng); Scrum ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát kế bên (A↔B, C↔D) trước khi merge.
- Cách làm việc với Git: mỗi file một chủ (xem plan); nhánh ngắn `a/…`, `b/…`, `c/…`, `d/…`, `git pull --rebase origin main` + chạy test trước khi push; chỉ C merge vào `main` và gắn tag `phase-n`.
