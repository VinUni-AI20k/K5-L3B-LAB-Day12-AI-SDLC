# Kế hoạch Phase 1 (PRD-0) — 60 phút

- **Mục tiêu:**
  - Hoàn thiện Core Simulation cho 2 chế độ: Buổi sáng (`gather`: bơi, oxy, ngạt, máu, giỏ LIFO, hái nút, bắt cá) và Buổi tối (`quan`: khách vào, đặt chỗ bàn, kiên nhẫn, bếp nấu, phục vụ, tính tiền, uy tín).
  - Vượt qua 100% bộ Test Contract hộp đen (`test_smoke_p1.py`, `test_python_starter_units.py`).
  - Đảm bảo tính tất định headless (`--seed 1 --ticks 600`), xuất log JSONL chuẩn vào `docs/proof/phase-1/`.
  - Hoàn thành hồ sơ nhóm: `TEAM.md`, `check_team.py` pass, 2 AI skills tại `.agents/skills/`.
  - Gắn tag `phase-1` trước mốc 1:00.

- **Việc / người / phụ thuộc:**
  1. **TV1 (Leader / Integrator):** Setup `TEAM.md`, cập nhật `game.contract.json` (`team_size: 5`), viết 2 AI skills tại `.agents/skills/`, cập nhật `AGENTS.md`, phụ trách merge và gắn tag `phase-1`.
  2. **TV2 (`sim/gather`):** Lập trình Lát 1 (Oxy, ngạt, máu, ngất, giỏ LIFO) và Lát 2 (Hái bông súng/điên điển, bắt cá, cập bến) tại `chonoi/sim/gather.py`.
  3. **TV3 (`sim/quan`):** Lập trình Lát 3 (Khách đến, chọn món, giữ chỗ bàn/kho, kiên nhẫn, bỏ về) và Lát 4 (Nấu nướng tại bếp, bưng bê, trả tiền, điểm uy tín) tại `chonoi/sim/quan.py`.
  4. **TV4 (`qa`):** Soạn test scenario biên (`tests/test_scenarios.py`), chạy headless xuất proof JSONL vào `docs/proof/phase-1/`, điền ma trận kiểm chứng `docs/verification/phase-1.md`.
  5. **TV5 (`client/ui` & PO):** Cập nhật `docs/clarify.md`, hoàn thiện HUD giao diện chơi trực tiếp trên web (`chonoi/web/index.html`) hỗ trợ demo.
  - **Phụ thuộc:** TV4 và TV5 phụ thuộc vào bản tích hợp `gather.py` & `quan.py` từ TV2 & TV3 để xuất proof và hiển thị HUD.

- **Rủi ro & Biện pháp giảm thiểu:**
  - *Rủi ro logic phức tạp gây chậm tiến độ:* Người dự phòng (TV1/TV4) hỗ trợ trực tiếp; ưu tiên hoàn thiện lõi tối thiểu để pass Test Contract trước.
  - *Rủi ro xung đột Git:* Phân chia quyền sở hữu file rạch ròi, tuyệt đối không sửa chéo file của nhau.
  - *Rủi ro trễ tag 1:00:* Đúng 00:55 thực hiện đóng băng code (code freeze), chạy xuất proof và gắn tag `phase-1` đúng giờ.
