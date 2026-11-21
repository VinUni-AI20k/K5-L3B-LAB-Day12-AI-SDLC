# TEAM

**Tên nhóm:** NhomABC  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Vũ Quang Huy | `huyvu-03` | `sim/gather` (M1: Sinh tồn) | Dev | Nguyễn Minh Quang (M2) |
| Nguyễn Minh Quang | `QuangNEU` | `sim/gather` (M2: Thu hoạch + Kho) | Dev | Vũ Quang Huy (M1) |
| Phùng Văn Thanh Cao | `ththanh8888` | `sim/quan` (M3: Khách) | Dev | Nguyễn Nhật Minh (M4) |
| Nguyễn Nhật Minh | `NhMinh-2610` | `sim/quan` (M4: Bếp + Kinh tế) | Dev | Phùng Văn Thanh Cao (M3) |
| Vũ Quang Thanh | `thanhvu101` | `client/ui` (M5: UI + Âm thanh + AI Harness) | UI / Harness | Nguyễn Như Duy An (M6) |
| Nguyễn Như Duy An | `K0heii` | `contracts/qa` (M6: Hợp đồng + Tích hợp) | PO / Integrator / Release | Vũ Quang Thanh (M5) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Nhóm chat chung + họp trực tiếp tại lớp.
- Khi bất đồng về thiết kế: Trao đổi tối đa 2 phút; không thống nhất thì Integrator/PO (Nguyễn Như Duy An — M6) quyết định và ghi lý do vào `docs/clarify.md`.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay trên kênh chung để người dự phòng (theo bảng trên) hỗ trợ hoặc nhận tiếp task.
- Giờ standup giữa phase: Giữa mỗi phase (Phase 1: 0:30) và code freeze trước hạn tag 15 phút (Phase 1: 0:45).
- Cách đọc code của nhau: M1 ↔ M2 (cùng file `gather.py`), M3 ↔ M4 (cùng file `quan.py`), M6 duyệt tích hợp & bằng chứng trước khi gắn tag.
- Cách làm việc với Git: Pull trước khi code, tách nhánh ngắn theo mã task (hoặc push thẳng khi đã báo cặp dùng chung file), luôn chạy `unittest` xanh trước khi đẩy; M6 (Nguyễn Như Duy An) chịu trách nhiệm gắn tag `phase-1`..`phase-4` và Release `v1.0.0`.
