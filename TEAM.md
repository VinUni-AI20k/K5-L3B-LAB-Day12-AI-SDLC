# TEAM

**Tên nhóm:** 6667  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Le Quy Toan | ToanLee5433 | `sim/gather` |Integrator |  `sim/quan`|
| Nguyễn Thành Nam | Ishodayo | `sim/quan` | — | `sim/gather`|
| Dam Hong Thai | itsbra1vo | `client/ui` | Scrum/Release|`qa`|
| Dư Văn Hùng| czx04 | `qa` | QA lead, PO | `client/ui` |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: https://discord.gg/JbVVFQ4eB
- Khi bất đồng về thiết kế: mỗi bên nói tối đa 2 phút; không thống nhất thì Integrator quyết (phần luật/yêu cầu mơ hồ thì PO quyết) và ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh nhóm kèm lỗi/đoạn đang kẹt; người dự phòng (cột cuối bảng) vào pair hoặc nhận việc.
- Giờ standup giữa phase: 3 phút tại giữa mỗi phase (0:30, 1:25, 2:10, 2:45) và trước khi gắn tag; ghi nhanh vào `docs/standup.md`.
- Cách đọc code của nhau (tùy chọn): mỗi người đọc lát kế bên (gather ↔ quan, ui ↔ qa) qua PR; cần ≥ 1 người duyệt, gấp thì xem trực tiếp rồi ghi người duyệt trong PR.
- Cách làm việc với Git: không push thẳng `main`; mỗi việc một nhánh ngắn (`<module>/<việc>`), chạy test xanh rồi mở PR gộp vào `main`; đổi hợp đồng thì commit riêng. Chỉ Integrator gắn tag `phase-n` sau khi chạy test tại `main`.
