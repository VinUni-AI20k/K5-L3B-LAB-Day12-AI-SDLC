# Kế hoạch Phase 1 (≤ 1 trang)

- Mục tiêu: hết 1:00 có `phase-1` chạy được: luật `gather` (oxy, ngạt, giỏ, hái, bắt cá, cập bến, kho) và luật `quan` (khách, giữ chỗ, bếp, bưng, tiền, uy tín) đúng PRD-0; headless xuất JSONL tất định (cùng seed thì giống từng byte); smoke test xanh; có bằng chứng trong `docs/verification/phase-1.md`.
- Việc / người / phụ thuộc (chi tiết và trạng thái ở Google Sheet phân công, tab "Phân công"; chưa có issue GitHub):
  - Kickoff 0:00–0:15, Lương (D): `TEAM.md`, `docs/contracts/`, kế hoạch này (P1-01 đến P1-03). A, B, C đọc hợp đồng trước khi viết luật.
  - 0:15–0:40, Nhật (A) gather lát 1 (P1-04); Tú (B) quán lát 3 (P1-06); Lương scenario và contract (P1-08).
  - 0:40–0:55, Nhật gather lát 2 (P1-05, sau P1-04); Tú quán lát 4 (P1-07, sau P1-06); Cường (C) test luật quán (P1-10) và giao diện sim ↔ UI (P1-15); Lương test luật gather (P1-09) và `clarify.md` (P1-11).
  - 0:45–1:00, Lương: chạy test và kiểm tất định (P1-12), ma trận truy vết (P1-13), gắn tag `phase-1` (P1-14). Cường ghi standup.
- Rủi ro:
  - PRD-0 mục E và F (tên sự kiện, thứ tự xử lý khách) chưa có trong repo: hỏi PO, ghi `docs/clarify.md`, tự đặt giả định hợp lý và ghi lại.
  - Lát 2 của A và lát 4 của B nằm ở đường găng, trễ thì test và tag trễ theo: báo trong kênh chung nếu vướng quá 10 phút, người dự phòng nhận việc.
  - Test mặc định gọi `python3`; trên Windows cần có `python3` trong PATH, nếu không 20 test lỗi `FileNotFoundError` dù code đúng.
  - Số liệu đọc từ `game.contract.json`, không hard-code trong luật; đổi khóa contract phải báo cả nhóm.
