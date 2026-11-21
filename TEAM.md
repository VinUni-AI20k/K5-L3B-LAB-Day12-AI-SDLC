# TEAM

**Tên nhóm:** Nicecentt  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| capkhai | `capkhai` | `sim/gather` | Dev Lead | `sim/quan` (`nhungvo631-stack`) |
| Võ Thị Phương Nhung | `nhungvo631-stack` | `sim/quan` (khách & hợp đồng) | Integrator | `sim/gather` (`capkhai`) |
| Vũ Văn Chủ | `chur04` | `sim/quan` (bếp & phục vụ) | PO | `sim/quan` (`nhungvo631-stack`) |
| Nguyễn Tiến Đạt | `duhocsinh4to10` | `client/ui` | Demo Lead | `harness/ops` (`VThanh-Huy`) |
| Nguyễn Minh Thành | `thanhhy98` | `qa` | QA Lead | `client/ui` (`duhocsinh4to10`) |
| Võ Thanh Huy | `VThanh-Huy` | `harness/ops` | Scrum / Release | `qa` (`thanhhy98`) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Nhóm chat chung (Zalo/Discord/Messenger) + GitHub repo `K5-L3B-LAB-Day12-AI-SDLC-Nicecentt`.
- Khi bất đồng về thiết kế: Thảo luận nhanh tối đa 2 phút; nếu chưa chốt, Integrator quyết định theo PRD/Contract và ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay trên kênh chung để người dự phòng nhận tiếp việc, không ôm lỗi một mình.
- Giờ standup giữa phase: Giữa mỗi phase (Phase 1 tại mốc 0:35), mỗi người ghi 1 dòng vào `docs/standup.md` trong 2–3 phút.
- Cách đọc code của nhau: Mỗi người đọc chéo diff của lát kế bên (qua PR hoặc xem trực tiếp) trước khi gộp vào `main`.
- Cách làm việc với Git: Tạo nhánh ngắn theo việc (`feat/<module>-<viec>`), chạy pass toàn bộ test trước khi merge vào `main`; Integrator chịu trách nhiệm gắn tag `phase-1`…`phase-4` và Release `v1.0.0`.
