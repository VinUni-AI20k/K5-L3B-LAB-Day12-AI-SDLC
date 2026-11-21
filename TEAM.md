# TEAM

**Tên nhóm:** ChoNoi  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| (điền tên) | HoangHongNgo | `docs/contracts`, `contract.py` (dải hợp lệ), tích hợp | PO + Integrator + Scrum/Release | RachalHys |
| Chu Nguyen Tung Duong | ChuTungDuongg | `sim/gather`, lát 1 (bơi, oxy, ngạt, Máu, giỏ) | Dev | haiquanng |
| Quan | haiquanng | `sim/gather`, lát 2 (hái, bắt cá, cập bến, file kho) | Dev | ChuTungDuongg |
| Nguyễn Minh Phương | minhphuong150505 | `sim/quan`, lát 3 (khách, giữ chỗ, kiên nhẫn) + `scenario.py` | Dev | phuthaitran |
| Tran Phu Thai | phuthaitran | `sim/quan`, lát 4 (bếp, bưng, phục vụ, tiền, uy tín) | Dev | minhphuong150505 |
| Nguyen Duc Khuong Lam | RachalHys | `client/ui` (HUD), README, test | QA lead | HoangHongNgo |

**Vai quy trình:** PO (đầu mối hỏi Anh Năm/giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gộp PR, gắn tag) · QA lead (bộ test + ma trận truy vết) · Scrum/Release (theo dõi mốc).

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: nhóm chat chung của lớp (Zalo/Messenger), mọi quyết định chốt ghi lại vào repo.
- Khi bất đồng về thiết kế: mỗi bên nói 2 phút; chưa xong thì Integrator (HoangHongNgo) quyết, ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng (cột trên) vào pair.
- Standup: phút 20 và phút 40 của mỗi phase, 2–3 phút (đã xong / sắp làm / đang vướng).
- Đọc code của nhau: lát 1↔2 và lát 3↔4 review chéo; PR đổi `docs/contracts/` hoặc `game.contract.json` cần thêm Integrator duyệt.
- Git: mỗi việc một nhánh ngắn `p1/<lát>-<tên>`, chạy test xanh rồi mở PR vào `main`; Integrator gộp và là người duy nhất gắn tag.
