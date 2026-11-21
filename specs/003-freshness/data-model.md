# Data model — Phase 3 (bổ sung 001, 002)

## Item
| Trường | Kiểu | Ràng buộc |
|---|---|---|
| `id` | chuỗi | duy nhất giữa giỏ, kho quán, phần giữ, Shop; khác rỗng; cấp `I1, I2…` theo thứ tự vào giỏ, không tái dùng |
| `kind` | chuỗi | 1 trong 6 nguyên liệu |
| `fresh` | số | [0,100]; nội bộ `units = round(fresh×240)`; ươn khi `units < 7200` |

Hao: giỏ `−round(0.5×240/60)=−2`/tick, kho quán `−1`/tick, kẹp 0. Không hao: món chín, Shop, khi pause, tick bàn giao.
`spoiled` phát khi `units_trước ≥ 7200` và `units_sau < 7200`.

## Hold / Stock
- `hold`: mảng Item theo thứ tự vào (cuối = mới nhất); LIFO khi `monster_hit`/ngất; ≤ 12.
- `stock` (quán, Shop): mảng Item sắp theo id; không giới hạn.

## Order (khách)
`reserved: [item_id]` (đủ công thức, cá thể chưa ươn, không dùng chung), `order_tick`, `order_status ∈ {reserved, unfulfillable, cooking, ready, …}` (GIẢ ĐỊNH tên), `base_price` (chốt lúc `cook_started`).
Chọn giữ chỗ: theo từng kind trong công thức (thứ tự kind sắp id), lấy n cá thể khả dụng có `units` lớn nhất, hòa id nhỏ.
Phần giữ vừa ươn: nhả hết → giữ lại đúng 1 lần (các đơn bị ảnh hưởng theo `(order_tick, table_id)`) → thiếu thì `unfulfillable` (khách vẫn chờ, kiên nhẫn chạy).

## Giá
`base_price = floor(price × mean(fresh của items dùng) / 100)` — tính bằng đơn vị: `floor(price × Σunits / (n × 240 × 100))`. `tip = floor(base_price × tip_rate)` nếu đủ điều kiện boa.

## File kho v1.2
`{"items":[{"id":"I1","kind":"ca_linh","fresh":100},...]}` sắp theo id; rỗng `{"items":[]}`. Xem [contracts/inventory-v1.2.md](contracts/inventory-v1.2.md).
