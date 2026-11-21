# 04: Quan customers — đến, giữ chỗ, kiên nhẫn, bỏ đi

**What to build:** Khách vào quán theo nhịp, gọi món trong số món nấu được với kho hiện có, và giữ chỗ nguyên liệu ngay khi gọi — để món họ gọi không bị dùng cho người khác. Chờ lâu thì bỏ đi và quán mất uy tín.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Khách đến ở `first_customer_tick`, sau đó mỗi `customer_interval_s × 60` tick, tính theo `phase_tick`; hết bàn trống thì bỏ lượt (không dồn khách).
- [ ] Khách mới lấy bàn trống có id nhỏ nhất; chọn **đều theo seed** trong các món đủ nguyên liệu khả dụng (tồn vật lý trừ phần đã giữ); không món nào đủ thì phát `no_dish` và không tạo khách.
- [ ] Khách mới giữ đúng công thức ngay khi gọi, `order_tick` bằng `phase_tick` hiện tại, kiên nhẫn đầy và **giảm từ bước sau**; phát `customer_arrived` `{order_id, table_id, dish_id}`.
- [ ] Hết kiên nhẫn khi còn giờ: khách rời, phát `customer_left` `{order_id, table_id, reason:"patience", reputation}`, uy tín `+left_reputation_delta`, nhả phần giữ chỗ.
- [ ] Khi khách rời: nhả giữ chỗ thô, bỏ món của đơn đang nấu/ready/trên tay; nguyên liệu đã dùng **không** hoàn lại.
- [ ] Fixture dựng được khách ở các trạng thái `reserved/assigned/unfulfillable/served`, và từ chối fixture mâu thuẫn bằng mã 2.
- [ ] `random_customers: false` không sinh khách; khách fixture vẫn dùng bình thường.
