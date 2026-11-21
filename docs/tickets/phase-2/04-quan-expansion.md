# 04: Quán 2 bếp / 4 bàn / 6 món / kế hoạch ngày

**What to build:** Quán đủ rộng để có áp lực: hai bếp nấu song song, bốn bàn, sáu món với hai nguyên liệu mới. Trong chế độ ngày, khách chỉ gọi món nằm trong kế hoạch Má Tư công bố.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Hai bếp B1 [2,8], B2 [5,8] và bốn bàn T1–T4; `interact` chọn gần nhất, hòa ưu tiên bếp trước bàn rồi id; tay cầm 1 món.
- [ ] Sáu món đúng công thức/giá/thời gian nấu; kho và file kho nhận `ca_keo`, `keo_neo`.
- [ ] Bếp lấy đơn `reserved` cũ nhất theo `order_tick` rồi id bàn; hai bếp có thể nấu hai đơn cùng lúc, không giẫm đơn của nhau.
- [ ] Trong `day`: lọc menu theo `day_plan.dishes` **trước**, rồi mới lọc nguyên liệu khả dụng (tồn − giữ chỗ); quán độc lập dùng cả 6 món.
- [ ] Khách vẫn đến theo nhịp 120 + 900·k, chọn đều theo seed trong các món đủ nguyên liệu; có bàn trống mà không món nào đủ → `no_dish`.
- [ ] Khách có thể gọi tiếp món đủ nguyên liệu kể cả khi đã bán đủ số suất kế hoạch (kế hoạch chỉ là mục tiêu thu gom, không phải trần bán).
- [ ] Fixture dựng được 4 bàn có khách, 2 bếp đang nấu, tay đang giữ món; dữ liệu mâu thuẫn → mã 2.
