# Kế hoạch Phase 1 (≤ 1 trang)

## 1. Mục tiêu
- Hoàn thiện toàn bộ khung quản trị nhóm, hợp đồng tích hợp và AI harness (Thành viên 1).
- Hoàn thành Lát 1 Gather Sim: chu trình Lặn/Nổi, Oxy, Ngạt, Máu/Ngất, Giỏ LIFO (Thành viên 2).
- Hoàn thành Lát 2 Gather Sim: Hái nút, Bắt cá, Nút hồi sinh, Cập bến và xuất kho nguyên tử (Thành viên 3).
- Toàn bộ test suite xanh 100%, chạy mượt mà ở chế độ headless và gắn tag `phase-1` trước mốc 1:00.

## 2. Việc / Người / Phụ thuộc
- **Thành viên 1 (`hieunhangia` - Integrator):**
  - Commit 1: Setup `TEAM.md` (khởi tạo vị trí Thành viên 1, placeholder các thành viên khác) và `game.contract.json` (`team_size = 6`).
  - Commit 2: Chốt hợp đồng tích hợp `docs/contracts/` và giải định `docs/clarify.md`.
  - Commit 3: Thiết lập 2 custom skills trong `.agents/skills/` và quy chuẩn `AGENTS.md`.
- **Thành viên 2 (`<github-handle-2>` - Dev Lead Gather):**
  - Commit 4: Cơ chế lặn/nổi (`dive`/`surface`) và tiêu hao/hồi phục oxy. *(Phụ thuộc Commit 3)*
  - Commit 5: Cơ chế ngạt nước (`choke`), trừ máu và ngất (`faint`/`fainted`). *(Phụ thuộc Commit 4)*
  - Commit 6: Tích hợp giỏ hàng `hold` cơ chế LIFO, sức chứa 12 và đồng bộ snapshot. *(Phụ thuộc Commit 5)*
- **Thành viên 3 (`<github-handle-3>` - Dev Gather Items):**
  - Commit 7: Hái nút bông ở mặt nước (`gather`/`hold_full`) và đếm lùi hồi sinh (`node_regrown`). *(Phụ thuộc Commit 6)*
  - Commit 8: Bắt đàn cá bằng phím `catch`, thời gian hồi chiêu và sự kiện `fish_caught`. *(Phụ thuộc Commit 7)*
  - Commit 9: Cập bến bến tàu (`docked`), hết giờ (`time`), ghi file kho và gắn tag `phase-1`. *(Phụ thuộc Commit 8)*

## 3. Quản lý rủi ro
- **Rủi ro xung đột mã nguồn:** Áp dụng nghiêm ngặt mô hình chuyền đuốc (Relay pipeline tuần tự 100%), không ai làm việc song song trên cùng nhánh `main`.
- **Rủi ro sai lệch dữ liệu tuning:** Mọi thông số đọc trực tiếp từ `tuning` trong contract, tuyệt đối không hardcode.
- **Rủi ro ngẫu nhiên không tất định:** Bắt buộc sử dụng bộ sinh ngẫu nhiên `Streams` được khởi tạo từ `seed`.
