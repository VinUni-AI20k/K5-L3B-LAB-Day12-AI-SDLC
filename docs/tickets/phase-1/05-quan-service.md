# 05: Quan service — nấu, bưng, phục vụ, tiền, boa, đóng ca

**What to build:** Người chơi nấu món đúng đơn đã giữ chỗ, bưng ra bàn trước khi khách hết kiên nhẫn, thu tiền và có thể được boa. Hết ca thì khách còn ăn vẫn trả tiền; khách còn chờ thì về, không trừ uy tín.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `interact` chỉ xử lý **một** đối tượng mỗi bước, chọn theo (khoảng cách, bếp trước bàn, id); đối tượng đã chọn mà không tương tác được thì **bỏ lượt**, không thử đối tượng khác.
- [ ] Bếp `idle` lấy đơn `reserved` cũ nhất (theo `order_tick`, rồi id bàn), tiêu đúng phần giữ chỗ, chốt `base_price`, bắt đầu nấu `cook_s × 60` tick; phát `cook_started` `{stove_id, order_id, dish_id, items, base_price}` với `items` sắp theo kind.
- [ ] Nấu xong: bếp `ready`, `ready_ticks = 0`, phát `dish_ready`; `ready_ticks` chỉ tăng cho món đã ready ở **đầu bước**.
- [ ] Bếp `ready` + tay trống: chuyển món vào tay (payload `{order_id, dish_id, base_price}`), bếp về `idle`, phát `dish_picked`.
- [ ] Bưng món tới bàn có khách đúng `order_id`: khách chuyển `eating` với timer ăn đầy, phát `served` `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}`.
- [ ] Boa = `floor(base_price × tip_rate)` nếu tỷ lệ kiên nhẫn **sau bước giảm** ≥ `tip_min_patience_ratio`, ngược lại 0; phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ.
- [ ] Ăn xong: phát `paid` `{order_id, table_id, base_price, tip, amount, reason:"finished_eating"}`, tiền/`earned`/`shift_earned` cộng đúng, uy tín `+tip_reputation` khi boa > 0 và kẹp trong `[min, max]`, khách rời bàn ngay.
- [ ] Hết ca: khách đang ăn trả ngay (kể cả vừa được giao món), khách còn chờ rời với `reason:"closing"` **không** trừ uy tín; dọn xong phát `quan_end` đúng một lần với `money, earned, shift_earned, reputation`.
- [ ] `score = earned + 100 × floor(reputation)` ở mọi snapshot và dòng `end`.
