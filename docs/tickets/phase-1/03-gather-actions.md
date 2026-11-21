# 03: Gather actions — hái, bắt cá, cập bến, ghi kho

**What to build:** Người chơi hái bông ở mặt nước, lặn bắt cá, rồi mang giỏ về bến. Cập bến là chốt sổ; hết giờ cũng chốt sổ; ngất thì mất trắng.

**Blocked by:** 01

**Status:** in-review

Helper và 25 test hộp đen đã hoàn thành, đã nối với core của Cao Minh từ commit `9342f9e`
trong bản làm việc trên `feat/nhat-minh`: **62/62 test qua**.
Patch, nguồn phần core và lệnh kiểm chứng: [bằng chứng Nhật Minh](../../proof/phase-1/nhat-minh.md).
Chờ Cao Minh review; chưa commit/push/merge thay đổi của Nhật Minh trong lượt này.

- [x] `interact` trong `dock_radius` → `gather_end` lý do `docked` **trước** mọi xử lý hái, không cần đang ở mặt nước.
- [x] Ngoài bến, chỉ hái khi ở mặt nước: nút `ready` gần nhất trong `interact_radius`, hòa khoảng cách thì id nhỏ hơn theo `id_key` (`N2` trước `N10`).
- [x] Đủ chỗ: thêm `node_yield` nguyên liệu, đặt `regrow_ticks = regrow_s × 60`, phát `gather` `{node_id, kind, amount}`; thiếu chỗ: `hold_full` `{action:"gather", node_id, required, free}`, nút **giữ nguyên** (không đặt mọc lại).
- [x] Nút về 0 phát `node_regrown` và hái lại được ngay bước đó.
- [x] `catch` khi hết hồi chiêu và đang dưới nước: chọn đàn gần nhất trong `catch_radius`, hòa thì id nhỏ hơn; đủ chỗ thì thêm toàn bộ `fish_yield`, **xóa đàn**, phát `fish_caught` `{fish_id, kind, yield}`, đặt hồi chiêu `catch_cooldown_s × 60`.
- [x] Thiếu chỗ: `hold_full` `{action:"catch", fish_id, required, free}`, giữ đàn, không thử đàn khác; không có đàn trong tầm: không event, không hồi chiêu.
- [x] File kho ghi đúng một lần khi `gather_end` (ngất ghi `{"items":{}}`), khớp `inventory` trong event; chạm `--ticks` trước khi kết thúc thì không tạo/ghi đè file.

AC cuối: đã kiểm cập bến, hết giờ, nội dung kho, tick limit (không tạo/ghi đè),
ngất mất giỏ LIFO và chặn tương tác/bắt cá. Nhánh ngất dùng test core của Cao Minh.
