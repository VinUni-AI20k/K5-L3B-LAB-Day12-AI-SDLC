# TEAM

**Tên nhóm:** ChoNoiCaMau  **Số người:** …  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Lê Đăng Khoa | s0ra1n0 | `sim/gather` (lát 1: oxy, ngạt, Máu, giỏ) | Integrator | `sim/gather` lát 2 |
| | | `sim/gather` (lát 2: hái, bắt cá) | | `sim/gather` lát 1 |
| | | `sim/quan` (lát 3: khách, giữ chỗ, kiên nhẫn) | PO | `sim/quan` lát 4 |
| | | `sim/quan` (lát 4: bếp, phục vụ, tiền, uy tín) | | `sim/quan` lát 3 |
| | | `qa` + `client/ui` + skills | QA lead, Scrum/Release | mọi lát (test) |

> Nhóm 4 người: xóa dòng cuối, người lát 4 hoặc lát 2 kiêm `qa`. Điền đủ tên + handle thật rồi chạy `python3 tools/check_team.py`.

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: … (đề xuất: nhóm chat chung + ngồi cạnh nhau)
- Khi bất đồng về thiết kế: nói tối đa 2 phút, không xong thì Integrator quyết và ghi lý do vào `docs/adr/` hoặc `docs/clarify.md`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng vào pair hoặc nhận việc.
- Giờ standup giữa phase: khoảng giữa mỗi phase (Phase 1: 0:35), 5 phút, ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi PR có ít nhất 1 người đọc (ưu tiên người dự phòng của lát đó).
- Cách làm việc với Git: nhánh ngắn `feat/<lát>` → PR nhỏ, chạy test xanh mới merge vào `main`; chỉ Integrator gắn tag `phase-n`.
