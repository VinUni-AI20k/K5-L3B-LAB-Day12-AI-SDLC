# TEAM

**Tên nhóm:** G2026  **Số người:** 3  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trương Đặng Minh Khuê | mKhaiTruong | `docs/contracts`, `scenario.py` (mã 2), `qa` (test, proof, verification) | Integrator (gắn tag) · QA lead | Khánh (`sim/quan`) |
| Phong | trinhtuanphong123 | `sim/gather` (lát 1 + 2), `README.md` | Scrum/Release | Khuê (`qa`) |
| Khánh | qockhah253 | `sim/quan` (lát 3 + 4) | PO (giữ `docs/clarify.md`) | Phong (`sim/gather`) |

> Chia theo **file** để không ai sửa chung một file: lát 1–2 cùng `chonoi/sim/gather.py` → Phong; lát 3–4 cùng `chonoi/sim/quan.py` → Khánh.
> `client/ui`: P1 dùng tạm `chonoi.live` (tự hiện trường có trong snapshot); Phong chơi thử HUD sau khi xong `gather`. Khuê xong contracts thì hỗ trợ Khánh lát 4 (`paid`/closing). Chi tiết: [`docs/plan/phase-1.md`](docs/plan/phase-1.md).

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: group chat của nhóm (chốt lại ở kickoff).
- Khi bất đồng về thiết kế: mỗi bên nói 2 phút; không xong thì Integrator (Khuê) quyết và ghi lý do vào `docs/adr/`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh; người dự phòng (cột cuối) nhận việc.
- Giờ standup giữa phase: giữa mỗi phase (~25 phút sau khi mở phase), ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát của người mình dự phòng, qua PR.
- Cách làm việc với Git: nhánh ngắn `<handle>/<việc>` → PR vào `main`, chạy test trước khi gộp; chỉ Integrator gắn tag.
