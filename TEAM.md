# TEAM

**Tên nhóm:** 4npc  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trần Quang Hà | tranha1764 | `sim/gather` | Integrator | `sim/quan` |
| Nguyễn Thành Tâm | ngthanhtamtb | `sim/gather` | PO | `sim/gather` |
| Mai Danh Hiếu | danhhieu204ns | `sim/quan` | Scrum/Release | `sim/quan` |
| Ngô Minh Cương | ngominhcuong | `sim/quan` | Dev | `sim/quan` |
| Nguyễn Quang Tiệp | nguyenquangtiep | `client/ui` | Dev | `qa` |
| Đoàn Trí Hùng | hungdt31 | `qa` | QA Lead | `client/ui` |

**Vai quy trình:** PO (đầu mối hỏi giảng viên/Anh Năm, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA Lead (bộ test, `docs/verification/`) · Scrum/Release (theo dõi mốc bàn giao). Có thể kiêm.

## Thỏa thuận làm việc nhóm (≤ 10 dòng)

- Kênh liên lạc: Nhóm chat chung của team (báo ngay khi vướng > 10 phút để người dự phòng hỗ trợ).
- Khi bất đồng về thiết kế: Thảo luận tối đa 2 phút, chưa chốt được thì Integrator quyết và ghi lý do.
- Giờ standup giữa phase: Phút 20–25 mỗi phase (nêu ngắn: đã xong / sắp làm / đang vướng), rà lát chậm để điều người hỗ trợ.
- Cách làm việc với Git: Nhánh ngắn (`feat/<module>-<desc>`, `fix/...`, `docs/...`) từ `main` → PR nhỏ (≤ ~400 dòng), CI `ci / test` pass + 1 review approve trước khi merge; không push trực tiếp làm vỡ `main`.
- Quy ước commit & đóng góp: `<type>(<scope>): <mô tả>`, mỗi thành viên ≥ 3 commit có nội dung bằng tài khoản GitHub của mình; pair thì ghi `Co-authored-by:`.
- Khóa hợp đồng & tag: Không tự ý sửa `game.contract.json` hay `docs/contracts/` khi chưa báo nhóm; Integrator merge và gắn tag `phase-1`..`phase-4` trên `main` đúng hạn.
