# 08: Mở rộng — Khách đặt trước (`reservations`)

**What to build:** Mỗi Ngày có 2 khách đặt bàn trước, đến vào giờ hẹn với món đã chọn. Giữ bàn từ 30 giây trước giờ hẹn; khách thường không được ngồi vào bàn đó.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Manifest `reservations {count: 2, table_hold_s: 30, price_multiplier: 1.5, failed_reputation_delta: -1}`; `extensions` có `reservations`.
- [ ] Công bố 2 đơn sau `phase_start(gather)` (quán độc lập: lúc dựng pha), hai bàn khác nhau, món trong kế hoạch, `arrival_tick` theo seed trong [1800, 10799].
- [ ] Trạng thái `scheduled → holding → waiting → served | failed`; giữ bàn từ `max(0, arrival_tick − 1800)`; khách thường đang ngồi được ở lại, khách mới không ngồi bàn giữ.
- [ ] Đến giờ: bàn còn khách → `failed(occupied)`; thiếu kho → `failed(stock)`; thành công → giữ nguyên liệu ngay, phát `reservation_arrived` rồi `customer_arrived`.
- [ ] Giá cuối `floor(giá_đã_chốt_theo_fresh × 1.5)` rồi mới tính boa; giao xong phát `served` rồi `reservation_served`.
- [ ] Lỡ đơn (stock/occupied/burnt/patience/closing): nhả hàng + bàn, hủy món, uy tín −1 **một lần**, phát `reservation_failed`; không cộng phạt khách thường.
- [ ] Đóng ca: fail các đơn chưa phục vụ theo id đặt; `served`/`failed` là trạng thái cuối.
- [ ] Snapshot quán có `customers[].reservation_id`, `tables[].reservation_id` (null khi không có); scenario nhận `quan.reservations[]`, `random_reservations:false`.
