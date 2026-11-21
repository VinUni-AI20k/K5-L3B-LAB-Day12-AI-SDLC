# Hợp đồng tích hợp — Nhóm Nicecentt (Contract v1.1)

> Người giữ hợp đồng (Integrator): **Võ Thị Phương Nhung (`nhungvo631-stack`)**.
> Khi cần đổi hợp đồng (schema kho, snapshot, tên sự kiện, `game.contract.json`): báo cả nhóm trước và ghi lại lý do trong `docs/adr/` hoặc `docs/clarify.md`.

---

## 1. Schema file kho (Contract G)

- **File mẫu hợp lệ:** [`inventory.sample.json`](./inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`
- **Cấu trúc bắt buộc:** đúng 1 khóa gốc `"items"`, giá trị là object `{<kind>: <số nguyên >= 0>}`.
- **Nguyên liệu hợp lệ v1.1:** `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, `ca_keo`, `keo_neo`.
- Hai nguyên liệu sáng tạo `ca_ro_dong`, `rau_muong` chỉ bật qua `--extra-content` ở `chonoi.live` (tắt mặc định ở headless).
- **Quy tắc đọc/ghi:**
  - Khi ghi (`chonoi/inventory.py`): loại bỏ mục có số lượng `0`, sắp khóa theo thứ tự bảng chữ cái, ghi nguyên tử qua file tạm.
  - Chỉ ghi **đúng 1 lần** khi `gather` kết thúc (`gather_end`). Nếu dừng do `tick_limit` thì **không ghi** file đích. Nếu kết thúc với `reason="fainted"` thì giỏ rỗng (`{"items":{}}`).
  - Trong `--mode day`: bàn giao kho tự động trong bộ nhớ giữa `gather` và `quan`; cấm `--inventory` / `--inventory-out` / `quan.stock` / `quan.reputation` (mã thoát `2`).

---

## 2. Giao diện giữa `sim/*` và `client/ui`

- **Nguyên tắc:** `client/ui` (`chonoi/web/index.html` qua `chonoi/live.py`) **chỉ đọc snapshot**, không chứa logic mô phỏng.

### Dữ liệu UI đọc (từ `Session.snapshot()`)
- **Trường chung:** `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`"playing"` | `"paused"` | `"finished"`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
- **Chế độ `day`:** bổ sung `day`, `day_plan`, `upgrades`, `active_upgrades`; `phase` là `"gather"`, `"quan"` hoặc `"shop"`. Snapshot `shop` có `stock` dư và `time_left_ticks`.
- **Chế độ `gather`:** `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`), `hold`, `hold_count`, `hold_capacity`, `nodes[]`, `fish[]`, `monsters[]`.
- **Chế độ `quan`:** `player` (`pos`), `stock`, `hand` (`{"order_id","dish_id","base_price"}` hoặc `null`), `stoves[]`, `tables[]`, `customers[]`.

### Lệnh UI gửi vào `sim` (`InputState` / `POST /input`)
- `move`: `[x, d]` (`gather`) hoặc `[x, z]` (`quan`), chuẩn hóa độ dài `<= 1`.
- Nút boolean cạnh lên (v1.1): `interact`, `catch`, `pause`, `shop_done`, `attack`, `photo`.
- Chuỗi chạy đúng 1 frame: `buy` (`"oxygen"`, `"hp"`, và mở rộng nếu bật).

---

## 3. Danh sách sự kiện (`type: "event"`)

Mỗi dòng sự kiện có dạng: `{"type":"event","tick":<int>,"phase":"gather"|"quan"|"shop","name":<str>,"data":{...}}` *(chế độ `day` thêm trường `"day"`).*

### Chế độ `gather`
| Tên sự kiện | `data` |
|---|---|
| `dive`, `surface` | `{"pos": [x, d]}` |
| `oxygen_empty` | `{"oxygen_ticks": 0}` |
| `choke` | `{"hp": <int>}` |
| `monster_hit` | `{"monster_id": <id>, "hp": <int>, "lost": [<kind>...], "pos": [x, d]}` (`lost` theo LIFO) |
| `faint` | `{"cause": "choke"\|"monster", "lost": [<kind>...], "hp": 0}` (`lost` theo LIFO) |
| `gather` | `{"node_id": <id>, "kind": <kind>, "amount": <int>}` |
| `node_regrown` | `{"node_id": <id>}` |
| `fish_caught` | `{"fish_id": <id>, "kind": <kind>, "yield": <int>}` |
| `fish_spawned` | `{"id": <id>, "kind": <kind>, "pos": [x, d]}` |
| `hold_full` | `{"action": "gather"\|"catch", "node_id"\|"fish_id": <id>, "required": <int>, "free": <int>}` |
| `gather_end` | `{"reason": "docked"\|"time"\|"fainted", "inventory": {"items": {...}}}` |

### Chế độ `quan`
| Tên sự kiện | `data` |
|---|---|
| `customer_arrived` | `{"order_id": <id>, "table_id": <id>, "dish_id": <id>, "reserved": {...}}` |
| `customer_left` | `{"order_id": <id>, "table_id": <id>, "reason": "patience"\|"closing", "reputation": <float>}` |
| `no_dish` | `{}` (có bàn trống nhưng không có món đủ kho khả dụng) |
| `cook_started` | `{"stove_id": <id>, "order_id": <id>, "dish_id": <id>, "items": [...], "base_price": <int>}` |
| `dish_ready`, `dish_picked` | `{"stove_id": <id>, "order_id": <id>, "dish_id": <id>}` |
| `served` | `{"order_id": <id>, "table_id": <id>, "dish_id": <id>, "patience_ticks_left": <int>, "base_price": <int>, "tip": <int>}` |
| `paid` | `{"order_id": <id>, "table_id": <id>, "base_price": <int>, "tip": <int>, "amount": <int>, "reason": "finished_eating"\|"closing"}` |
| `quan_end` | `{"reason": "time", "money": ..., "earned": ..., "shift_earned": ..., "reputation": ...}` |

### Chế độ `day`, Shop & Pause
| Tên sự kiện | `data` |
|---|---|
| `day_start`, `phase_start`, `paused`, `resumed` | `{}` |
| `day_plan` | `{"dishes": {...}, "ingredients": {...}}` |
| `bought` | `{"upgrade": <id>, "level": <int>, "price": <int>, "money": <int>}` |
| `buy_failed` | `{"action": <str>, "reason": "funds"\|"max_level"\|"out_of_stock"\|"unknown"}` |
| `shop_end` | `{"reason": "done"\|"time"}` |
