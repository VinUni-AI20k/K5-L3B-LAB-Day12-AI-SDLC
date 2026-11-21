# Kế hoạch Phase 1 (≤ 1 trang)

- Mục tiêu: chơi được 2 buổi (gather, quan) đúng lõi PRD, đủ Test Contract v1.0, smoke 2 tiến trình xanh trên `main`, tag `phase-1` trước 1:00. Nhóm 6 người: thêm ít nhất 2 mục mở rộng (PO chốt ở phút 15).
- Việc / người / phụ thuộc (chi tiết ở `TEAM.md`):
  - [x] Lát 1 — bơi, oxy, ngạt, ngất, giỏ — Hưng — khung sẵn có
  - [x] Lát 2 — hái, bắt cá, cập bến, ghi kho — Phát — 22 test mới xanh, smoke kho thật; toàn bộ 71 test xanh sau gộp main, payload khớp hợp đồng; proof: `docs/proof/phase-1/lat2-phat/`. Cooldown khi hụt chờ PO xác nhận ở `docs/clarify.md`.
  - [ ] Lát 3 — khách, giữ chỗ, kiên nhẫn, no_dish — Minh — kho mẫu `docs/contracts/inventory.sample.json`
  - [x] Lát 4 — bếp, bưng, phục vụ, tiền, uy tín, quan_end — Diệp — trạng thái khách/đơn của lát 3
  - [ ] HUD 2 buổi + mở rộng #1 — Nhài — snapshot của các lát
  - [ ] Test theo AC, smoke, ma trận truy vết, proof + mở rộng #2 — Khang — PRD
  - [x] Hợp đồng kho + sự kiện sim↔UI trong `docs/contracts/` — Diệp — trước phút 15 (xong; mục [GĐ] chờ PO xác nhận, clarify #6)
  - [x] `team`/`team_size` trong `game.contract.json` khớp `TEAM.md` (doctorx, 6) — Diệp
  - [ ] Gộp các lát vào `main`, smoke 2 tiến trình trên `main`, tag `phase-1` — Diệp — phút 45–60
- Rủi ro:
  - Lát 3 và 4 cùng sửa `chonoi/sim/quan.py` → chốt tên trường khách/đơn sớm, tách hàm riêng, gộp thường xuyên.
  - Lát 1 và 2 cùng sửa `chonoi/sim/gather.py` → mỗi lát một hàm (`_oxygen`, `_interact`, `_catch`), gộp sau mỗi bước nhỏ.
  - Thứ tự xử lý trong bước (mục F) sai làm lệch tick event → QA viết test tick chính xác trước.
  - Phần mở rộng làm đổi kết quả headless → bắt buộc tắt ở headless, có test chứng minh.
