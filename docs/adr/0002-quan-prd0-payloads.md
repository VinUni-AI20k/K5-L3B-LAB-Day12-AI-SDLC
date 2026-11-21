# ADR 0002 — Đồng bộ Quán theo PRD-0

**Trạng thái** · Chờ Integrator đối chiếu và duyệt trước khi cập nhật bảng hợp đồng dùng chung.

Gói bàn giao TV4 mô tả thứ tự xử lý và payload Quán theo PRD-0 D/E/F. Bản trên `main` dùng tên món dạng chuỗi ở bếp và tay, nên cùng một món có thể được đưa cho khách khác đơn. `QuanSim` gắn món với đúng đơn từ lúc bắt đầu nấu đến khi phục vụ. Bộ nạp scenario kiểm tra các liên kết và tổng giữ chỗ dựa trên kho thực tế. HUD đọc `dish_id` từ món ở bếp.

Trong mỗi tick, cập nhật bộ đếm, di chuyển, xử lý tối đa một tương tác với vật gần nhất, rồi thanh toán hoặc cho khách rời bàn. Lượt khách mới đến sau khi chỗ và nguyên liệu được giải phóng. Ca kết thúc sau khi thu tiền khách đang ăn và cho khách đang chờ rời bàn.

## Payload cho bộ đọc Quán

- Snapshot `hand` và `stoves[].dish` chứa `{order_id, dish_id, base_price}` hoặc `null`. Khách có `dish_id`, `order_tick`, `patience_ticks_left`, `order_status`, `reserved`, `base_price` và `tip`.
- `customer_arrived` có `order_id`, `table_id`, `dish_id`. `no_dish` có `{}`. `customer_left` có `order_id`, `table_id`, `reason` (`patience` hoặc `closing`) và `reputation`.
- `cook_started`, `dish_ready`, `dish_picked` có `stove_id`, `order_id`, `dish_id`. `cook_started` còn có `items` và `base_price`.
- `served` có `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip`. `paid` có `order_id`, `table_id`, `base_price`, `tip`, `amount` và `reason` (`finished_eating` hoặc `closing`).
- `quan_end` có `reason`, `money`, `earned`, `shift_earned`, `reputation`. `score` nằm ở snapshot và dòng `end` của runner.

Bộ nạp nhận `dish` và `patience_ticks` trong fixture khách cũ. Bộ đọc JSONL ở lượt QA cần dùng payload mới. Xem lệnh và kết quả ở [kiểm chứng Phase 1](../verification/phase-1.md#kiểm-chứng-tv4).
