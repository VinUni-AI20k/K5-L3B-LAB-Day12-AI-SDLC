# 03: Quán — kho cá thể, giữ theo id, giá theo độ tươi

**What to build:** Quán nhận kho có tuổi: khách giữ đúng những con tươi nhất, con đang giữ mà ươn thì trả lại và giữ lần nữa, và giá món phản ánh độ tươi thực dùng.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Kho quán là mảng cá thể; hao 1 đơn vị/tick (0.25/s) kể cả hàng đang giữ chỗ; pause dừng hao.
- [ ] Đầu bước: hao kho thô → phát hết `spoiled {..., location:"stock"}` theo id → **rồi** mới xử lý giữ chỗ bị ươn.
- [ ] Giữ chỗ theo id: mỗi dòng công thức lấy cá thể tươi nhất khả dụng, hòa theo id; `reserved` là **mảng id**; không dùng chung giữa hai đơn.
- [ ] Nếu một cá thể đang giữ vừa ươn: nhả **toàn bộ** phần giữ của đơn, thử giữ lại **đúng một lần**; xử lý các đơn bị ảnh hưởng theo `order_tick` rồi id bàn; không đủ → `unfulfillable`, khách chờ tới hạn.
- [ ] Bắt đầu nấu: tiêu đúng các id đang giữ, chốt `base_price = floor(giá_niêm_yết × trung_bình_fresh_của_các_id_dùng / 100)`; `cook_started.items` là mảng cá thể sắp theo `(kind, id)`.
- [ ] Boa tính trên giá đã chốt; điểm vẫn `earned + 100 × floor(reputation)`.
- [ ] Không được giữ/nấu cá thể ươn; đơn không đủ sau khi thử lại thì `unfulfillable` đúng luật.
- [ ] Test: giá lẻ (làm tròn xuống), giữ chỗ có con vừa ươn, `unfulfillable`, `spoiled` ở stock, pause giữa lúc hao.
