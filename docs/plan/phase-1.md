# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** tag `phase-1` trước 1:00 với headless đúng Test Contract cho `gather` và `quan`, test xanh, giấy tờ tối thiểu đủ.
- **Việc / người / phụ thuộc** (theo bảng phân công 5 người):

| Việc | Người | Phụ thuộc | Trạng thái |
|---|---|---|---|
| `TEAM.md`, `team_size: 5`, hợp đồng chung `docs/contracts/` | TV1 | — | chưa |
| `gather` lát 1–2 (oxy, ngạt, Máu, giỏ, hái, bắt cá) + test | TV1 | hợp đồng | chưa |
| `quan` lát 3 (khách, giữ chỗ, kiên nhẫn, `no_dish`, `customer_left`) + kiểm scenario mã 2 + test | TV2 | hợp đồng | **xong, đã đối chiếu PRD-0** (câu mở Q14–Q19 ở `docs/clarify.md`) |
| `docs/prd/PRD-0.md`, `docs/clarify.md`, `docs/contracts/quan.md`, kế hoạch này | TV2 | — | xong |
| `quan` lát 4 (bếp, bưng, phục vụ, trả tiền, boa, uy tín) + test tích hợp gather → quan | TV3 | cấu trúc khách ở `docs/contracts/quan.md` | xong trên nhánh `Manh` (đã gộp lát 3) |
| UI/HUD `chonoi/web/index.html`, standup, CHANGELOG/CREDITS | TV4 | snapshot trong hợp đồng | chưa |
| Test AC hộp đen, ≥ 2 skill/hook, `docs/verification/phase-1.md`, `docs/proof/phase-1/` | TV5 | `TEAM.md` | chưa |

- **Rủi ro:**
  - Còn 6 câu mở về quán (Q14–Q19 trong clarify). *Giảm:* PO hỏi Anh Năm trên lab board, đổi giả định thì báo TV3.
  - TV2 và TV3 cùng sửa `chonoi/sim/quan.py` → conflict. *Giảm:* lát 3 nằm trong các hàm riêng (`_tick_patience`, `_spawn_customer`, ...), lát 4 viết hàm mới và chỉ thêm lời gọi ở chỗ `TODO(nhóm, lát 4 — TV3)` trong `step`.
  - `tests/test_team_check.py::test_template_is_rejected` đọc `TEAM.md` thật → sẽ đỏ khi TV1 điền TEAM.md. *Giảm:* TV5 đổi test sang dùng chuỗi mẫu, ghi lý do trong commit.
- **Đóng băng code:** 0:50 để TV5 chạy kiểm chứng, TV1 gắn tag.
