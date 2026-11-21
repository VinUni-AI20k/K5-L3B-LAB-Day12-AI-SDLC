# TEAM

**Tên nhóm:** NhomF7  **Số người:** 7  (khớp `team_size` trong `game.contract.json`; đề ghi 4–6 người, xem `docs/clarify.md` #1)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| invzble-z (chủ repo, điền tên thật) | invzble-z | `docs/contracts/`, `game.contract.json`, khung `step()` | Integrator (gộp, gắn tag, Release) | QA (WorkOfMinh) |
| Nguyễn Anh Dương | nganhduong123 | `docs/`, `.agents/skills/`, `AGENTS.md` | PO | Integrator (invzble-z) |
| Nguyễn Anh Tú | comtrang378-ship-it | `sim/gather` lát 1: oxy, ngạt, Máu, ngất | Dev | gather lát 2 (NguyenQuangDunghe161764) |
| Nguyễn Quang Dũng | NguyenQuangDunghe161764 | `sim/gather` lát 2: hái, bắt cá, giỏ | Dev | gather lát 1 (comtrang378-ship-it) |
| Trần Quốc | Quoosc | `sim/quan` lát 3: khách, giữ chỗ, kiên nhẫn | Dev | quan lát 4 (ttkien0710) |
| Trần Trung Kiên | ttkien0710 | `sim/quan` lát 4: bếp, bưng, phục vụ, tiền | Dev | quan lát 3 (Quoosc) |
| WorkOfMinh (điền tên thật) | WorkOfMinh | `qa`: test hộp đen theo AC, `scenario.py`, proof | QA lead + Scrum | PO (nganhduong123) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (đề xuất, chốt lại trong 15 phút kickoff)

- Kênh liên lạc: nhóm chat chung; việc gấp thì nói trực tiếp.
- Mỗi file chỉ có một chủ (xem bảng). Muốn sửa file của người khác thì báo chủ file trước.
- Khi bất đồng về thiết kế: mỗi bên nói 2 phút; chưa xong thì Integrator quyết và ghi lý do vào ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng vào giúp.
- Standup 3 phút ở giữa mỗi phase (P1 lúc 0:30); PO ghi `docs/standup.md`.
- Đọc code của nhau: người dự phòng review PR của lát mình dự phòng (nhận xét bám diff).
- Git: mỗi lát một nhánh ngắn `p<n>/<lát>`, PR nhỏ, chạy test trước khi mở PR; Integrator gộp và là người duy nhất gắn tag.
