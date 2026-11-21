# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Quy ước: **Trạng thái** = `chốt` (PRD / Anh Năm hàng xóm / giảng viên đã xác nhận) hoặc `giả định` (nhóm tạm làm theo, PO đang hỏi). Code làm theo cột "Trả lời / giả định"; đổi thì cập nhật dòng này và [`docs/contracts/README.md`](contracts/README.md).
> 2026-11-21 08:02: PRD-0 phát hành, đối chiếu lại toàn bộ câu 1–11.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Trạng thái | Ai quyết |
|---|---|---|---|---|---|
| 1 | 2026-11-21 0:10 | Khi `fainted`, file kho ghi gì? | Ghi `{"items":{}}`, đúng một lần. Giỏ bỏ theo LIFO, liệt kê ở `faint.data.lost`. | chốt — PRD-0 F, G | PO |
| 2 | 2026-11-21 0:10 | Chạy hết `--ticks` mà chưa `gather_end` thì có ghi kho không? | Không tạo, không ghi đè file. | chốt — PRD-0 G | PO |
| 3 | 2026-11-21 0:10 | `interact` trong vùng bến và cạnh nút hái cùng lúc? | Xét bến trước (khoảng cách tới tâm bến, tính cả đúng mép) → `docked`, không hái. | chốt — PRD-0 F | PO |
| 4 | 2026-11-21 0:12 | Ranh giới "dưới nước"? | `d ≤ 0.5` là mặt nước. dive/surface so đầu và cuối bước; oxy theo d cuối bước. Nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, không ngạt. | chốt — PRD-0 F | PO |
| 5 | 2026-11-21 0:12 | Giỏ không đủ chỗ cho cả mẻ cá? | `hold_full` (`action:"catch"`, `fish_id`, `required`, `free`), không nhận con nào, giữ đàn, **không** đặt hồi chiêu, không thử đàn khác. | chốt — PRD-0 F | PO |
| 6 | 2026-11-21 0:15 | Tên và `data` của các sự kiện gather/quan? | Theo bảng PRD-0 mục E, đã chép vào contracts mục 3 (khác bản nháp ở `gather`, `fish_caught`, `hold_full`, `oxygen_empty`, `faint` và toàn bộ sự kiện quan). | chốt — PRD-0 E | PO |
| 7 | 2026-11-21 0:15 | Bắt cá xong đàn cá biến mất hay mọc lại? | Xóa đàn khỏi `fish[]`. Phase 1 cá đứng yên, không sinh thêm. | chốt — PRD-0 F | PO |
| 8 | 2026-11-21 0:18 | Khách chọn món thế nào khi nhiều món nấu được? | Chọn đều theo seed trong các món đủ nguyên liệu khả dụng (tồn vật lý − phần giữ), duyệt id món theo Unicode; giữ đúng công thức ngay khi tới. | chốt — PRD-0 F | PO |
| 9 | 2026-11-21 0:18 | Không có bàn trống khi tới lịch khách? | Bỏ lượt, không phát sự kiện. Có bàn mà không món nào đủ → `no_dish` `{}`. | chốt — PRD-0 F | PO |
| 10 | 2026-11-21 0:20 | `burn_s = null` nghĩa là gì? | Món chín không cháy; `ready_ticks` là tuổi món trên bếp, chỉ tăng cho món đã ready từ đầu bước. | chốt — PRD-0 A, F | PO |
| 11 | 2026-11-21 0:20 | Uy tín kẹp thế nào, boa làm tròn ra sao? | Kẹp `[reputation_min, reputation_max]`. Boa = `floor(base_price × tip_rate)` nếu tỷ lệ kiên nhẫn còn lại sau bước 1 ≥ `tip_min_patience_ratio`, không thì 0; boa dương cộng `tip_reputation` khi thu tiền. | chốt — PRD-0 F | PO |
| 12 | 2026-11-21 10:28 | Id khách (cũng là `order_id`) đặt theo mẫu nào? | Tiền tố `C` cộng số thứ tự cấp qua `IdAllocator`: `C1`, `C2`… Khách luôn dùng `order_id` trùng id khách. | chốt — PO quyết (PRD-0 không nói) | PO |
| 13 | 2026-11-21 10:28 | Scenario không khai `reserved` mà kho không đủ nguyên liệu cho đơn có sẵn thì sao? | Coi là input lỗi: thoát mã 2, **không** tự chuyển đơn sang `unfulfillable`. | chốt — PO quyết (PRD-0 không nói) | PO |
