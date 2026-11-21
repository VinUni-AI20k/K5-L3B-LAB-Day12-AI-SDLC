# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| C-01 | 2026-11-21 Phase 1 | `hold_full` khi hái: `required` là gì? | Giả định: `required = node_yield` (1), `free = hold_capacity − số món trong giỏ`. Khi bắt: `required = fish_yield[kind]`. | Nhóm (chưa hỏi Anh Năm) |
| C-02 | 2026-11-21 Phase 1 | Id khách sinh mới dùng tiền tố nào? | Giả định: `C` + số (`C1`, `C2`…), nối sau hậu tố lớn nhất đã nạp qua `IdAllocator`. `order_id` = id khách. | Nhóm |
| C-03 | 2026-11-21 Phase 1 | Khách đang chờ có `base_price`/`tip` không? | Giả định: `null` cho tới khi chốt (giá chốt lúc `cook_started`, boa chốt lúc `served`). | Nhóm |
| C-04 | 2026-11-21 Phase 1 | Đơn `reserved` trong fixture thiếu `reserved` mà kho không đủ? | Giả định: chuyển `unfulfillable`, giữ chỗ rỗng (cấp theo `order_tick` rồi id bàn). | Nhóm |
| C-05 | 2026-11-21 Phase 1 | Khách ăn xong đúng tick hết ca: `paid` lý do nào? | Giả định: ưu tiên `finished_eating` (timer ăn về 0 xét trước), còn lại trả `closing`. | Nhóm |
| C-06 | 2026-11-21 Phase 1 | Bếp idle mà không có đơn reserved, hoặc tay đang cầm món mà bấm vào bếp ready? | Bỏ lượt, không event (mục F.3 "không tương tác được thì bỏ lượt"). | Nhóm |
| C-07 | 2026-11-21 Phase 1 | `invuln_ticks` (có trong khung) có chặn ngạt không? | Không — v1.0 không nhắc bất tử; chỉ đếm lùi, không ảnh hưởng luật. | Nhóm |
| C-08 | 2026-11-21 Phase 1 | Cộng dồn uy tín 0.2 bằng số thực có thể ra 3.9999… làm `floor` sai | Làm tròn 9 chữ số sau mỗi lần đổi uy tín rồi kẹp theo tuning. | Nhóm |
