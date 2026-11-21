# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Quy ước: **Trạng thái** = `chốt` (PO/giảng viên đã xác nhận) hoặc `giả định` (nhóm tạm làm theo, PO đang hỏi). Code làm theo cột "Trả lời / giả định" cho tới khi đổi; đổi thì cập nhật dòng này và [`docs/contracts/README.md`](contracts/README.md).

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Trạng thái | Ai quyết |
|---|---|---|---|---|---|
| 1 | 2026-11-21 0:10 | Khi `fainted`, file kho ghi gì? | Ghi `{"items":{}}` (mất toàn bộ giỏ), vẫn ghi đúng một lần. | chốt (theo TODO khung + PRD-0 G) | PO |
| 2 | 2026-11-21 0:10 | Chạy hết `--ticks` mà chưa `gather_end` thì có ghi kho không? | Không; giữ nguyên file đích (smoke test `tick_limit` kiểm). | chốt | PO |
| 3 | 2026-11-21 0:10 | `interact` trong vùng bến và cạnh nút hái cùng lúc thì làm gì? | Cập bến trước (`gather_end docked`), không hái. | chốt (khung) | PO |
| 4 | 2026-11-21 0:12 | Ranh giới "dưới nước": `d > surface_depth` hay `d >= surface_depth`? | `d <= surface_depth` là mặt nước; `d > surface_depth` là dưới nước. dive/surface so vùng đầu và cuối bước; oxy tính theo d **cuối** bước. | chốt (khung `_at_surface`) | PO |
| 5 | 2026-11-21 0:12 | Bắt cá được bao nhiêu con, giỏ còn ít chỗ hơn `fish_yield` thì sao? | Nhận `fish_yield[kind]` con (ca_linh 3, ca_loc 1). Giỏ không đủ chỗ cho **cả** mẻ → `hold_full`, không nhận con nào, đàn cá còn nguyên. | giả định | PO |
| 6 | 2026-11-21 0:15 | Tên sự kiện khách tới và `data` của các sự kiện quan / `oxygen_empty` / `choke` / `faint` / `gather` / `fish_caught` / `hold_full`? | Dùng bảng đề xuất trong `docs/contracts/README.md` mục 3 (nhãn [giả định]). | giả định — hỏi PRD-0 mục E | PO |
| 7 | 2026-11-21 0:15 | Bắt cá xong đàn cá biến mất hay mọc lại? | Biến mất khỏi `fish[]` trong phase 1 (cá đứng yên, không sinh thêm). | giả định | PO |
| 8 | 2026-11-21 0:18 | Khách chọn món thế nào khi nhiều món nấu được? | Chọn bằng `Streams` (seed) trong các món đủ nguyên liệu **sau khi trừ phần đã giữ**, rồi giữ chỗ ngay khi khách tới. | giả định | PO |
| 9 | 2026-11-21 0:18 | Không có bàn trống khi tới lịch khách? | Bỏ lượt đó, không phát sự kiện, lịch vẫn chạy tiếp. | giả định | PO |
| 10 | 2026-11-21 0:20 | `burn_s = null` nghĩa là gì? | Món chín không bao giờ cháy ở phase 1; `ready_ticks` chỉ đếm lên. | giả định | PO |
| 11 | 2026-11-21 0:20 | Uy tín kẹp thế nào, boa làm tròn ra sao? | Kẹp `[reputation_min, reputation_max]` sau mỗi thay đổi. Tiền boa = `floor(price * tip_rate)` (số nguyên). | giả định | PO |
