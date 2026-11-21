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
- **Thành viên 2 (Phạm Lý Ngọc Đức, `Ducbaynao` - Dev Lead Gather):**
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

## 4. Kết quả phần việc của tôi — Thành viên 2
- Tôi đã hoàn thành phần triển khai tương ứng commit 4–6: chuyển vùng, oxy, ngạt/ngất, giỏ có giới hạn và snapshot.
- Sau đối chiếu PRD-0, tôi sửa payload oxy/ngất, `lost` LIFO và helper giỏ nhận đủ lô. Tôi giữ 13 test unit, bổ sung 2 test CLI và chạy toàn bộ 70 test sau tích hợp TV3–5; tất cả qua. Tôi lưu [bằng chứng mới](../proof/phase-1/member-2/prd-correction/summary.json) và giữ log cũ để truy vết.
- Tôi đã nối helper giỏ vào đường hái/bắt của TV3, giữ nguyên quy tắc thiếu chỗ thì phát `hold_full` và không thay đàn/cooldown. Lần sửa nằm trên nhánh `fix/ducbaynao-gather-prd-payloads`, chờ review tích hợp.
- Tôi ghi nhận `check_team.py` còn chưa đạt vì thành viên 6 chưa điền handle. DoD toàn Phase 1 gồm cả quán, HUD và tag trên main; nhóm cần kiểm chứng riêng các mục đó.

## 5. Bàn giao sang Phase 2

- [Kế hoạch của TV4](phase-2.md) tiếp nối hợp đồng kho của Phase 1. Kiểm chứng phần quán dùng cả fixture riêng và file kho mẫu theo schema tích hợp.
