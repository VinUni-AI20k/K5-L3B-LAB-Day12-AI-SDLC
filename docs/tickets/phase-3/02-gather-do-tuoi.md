# 02: Lặn — id, độ tươi, hao, `spoiled`, mất hàng LIFO

**What to build:** Mỗi con cá/bông hái được là một cá thể có tuổi. Hàng trong giỏ hao nhanh, ươn thì không nấu được, và bị cắn thì mất con mới nhất trước.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Hái/bắt tạo cá thể mới với `fresh = 100` và id tự cấp; `gather`/`fish_caught` phát cá thể vừa nhận (ít nhất `item_ids`).
- [ ] Đầu mỗi bước: hàng **có sẵn** trong giỏ hao 2 đơn vị/tick (0.5/s), kẹp đáy 0; hàng mới nhận không hao ở bước đó.
- [ ] `fresh` đi từ ≥ 30 xuống < 30 → phát `spoiled {item_id, kind, location:"hold"}` **đúng một lần**, theo id nếu nhiều cá thể cùng vượt.
- [ ] `fresh` so ngưỡng trên số nguyên (7 200), không so trên số đã làm tròn.
- [ ] Giỏ đầy tính cả hàng ươn (vẫn chiếm ô); `hold_full` giữ nguyên payload như v1.1.
- [ ] Bị Cá Sấu cắn / ngất: mất hàng theo **LIFO trên mảng cá thể**; `lost` trong `monster_hit`/`faint` là mảng cá thể (id, kind, fresh), không còn là mảng kind.
- [ ] Pause đóng băng cả hao tươi; hết giờ/cập bến bàn giao nguyên trạng độ tươi hiện có.
- [ ] Test: fixture `fresh: 30` → `spoiled` ở tick 1; nhiều cá thể vượt ngưỡng cùng tick → event theo id; hai lần chạy cùng seed → cùng byte.
