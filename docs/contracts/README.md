# Hợp đồng tích hợp (chốt ở kickoff Phase 1)

Nguồn: PRD-0 §6.1 + Test Contract §E, §G. Chi tiết từng khóa: `docs/plan/phase-1-conformance.md`.

## 1. Schema file kho (gather → quan)

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Chỉ khóa gốc `items`; kind ∈ `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`; giá trị nguyên ≥ 0.
- Kind vắng = 0; bên ghi bỏ khóa lượng 0; kho rỗng `{"items":{}}`.
- Bên đọc từ chối sai schema / kind lạ / số âm → mã 2.
- Chỉ ghi khi `gather_end` (ngất ghi rỗng); chạm `--ticks` trước khi kết thúc thì **không** tạo/ghi đè file.

## 2. Giao diện `sim/*` ↔ `client/ui`

**Client chỉ đọc**, không ghi vào sim:

| Việc | Cách |
|---|---|
| Lấy trạng thái | `GET /state` → snapshot (cùng trường như dòng `snapshot` của headless) + `meta`, `events`, `finished`, `reason` |
| Gửi điều khiển | `POST /input` `{"move":[x,y], "interact":bool, "catch":bool}` (trạng thái phím **đang giữ**) |
| Chơi lại | `POST /restart` |

Trường client dùng (thiếu thì bỏ qua, không lỗi): `mode, tick, time_left_ticks, player.{pos,vel,heading_deg,oxygen_ticks,oxygen_max_ticks,hp,hp_max,at_surface}, hold, hold_count, hold_capacity, nodes[], fish[], stock, hand, stoves[], tables[], customers[], money, earned, reputation, score, events[], finished, reason`.

**Client không bao giờ** gửi thời gian, RNG hay quyết định luật. Mọi thứ sáng tạo (hạt nước, âm thanh, parallax) nằm ngoài `chonoi/` và không đổi snapshot.

## 3. Danh sách sự kiện

| Name | Data | Phát bởi |
|---|---|---|
| `gather` | `node_id, kind, amount` | gather |
| `node_regrown` | `node_id` | gather |
| `hold_full` | `action`, `node_id` hoặc `fish_id`, `required`, `free` | gather |
| `fish_caught` | `fish_id, kind, yield` | gather |
| `dive` / `surface` | `pos` | gather |
| `oxygen_empty` | `oxygen_ticks: 0` | gather |
| `choke` | `hp` (sau trừ) | gather |
| `faint` | `cause:"choke", lost:[...], hp:0` | gather |
| `gather_end` | `reason`, `inventory` | gather |
| `customer_arrived` | `order_id, table_id, dish_id` | quan |
| `no_dish` | `{}` | quan |
| `cook_started` | `stove_id, order_id, dish_id, items, base_price` | quan |
| `dish_ready` | `stove_id, order_id, dish_id` | quan |
| `dish_picked` | `stove_id, order_id, dish_id` | quan |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | quan |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` | quan |
| `customer_left` | `order_id, table_id, reason, reputation` | quan |
| `quan_end` | `reason:"time", money, earned, shift_earned, reputation` | quan |

Đổi tên event / đổi khóa payload = phá hidden test. Thêm event mới thì phải báo cả nhóm và không được đổi thứ tự event cũ.
