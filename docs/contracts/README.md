# Hợp đồng tích hợp — Nhóm Nicecentt (Contract v1.1)

> Người giữ hợp đồng (Integrator): **Võ Thị Phương Nhung (`nhungvo631-stack`)**.
> Khi cần đổi hợp đồng (schema kho, snapshot, tên sự kiện, `game.contract.json`): báo cả nhóm trước và ghi lại lý do trong `docs/adr/` hoặc `docs/clarify.md`.

---

## 1. Schema file kho (Contract G)

- **File mẫu hợp lệ:** [`inventory.sample.json`](./inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`
- **Cấu trúc bắt buộc:** đúng 1 khóa gốc `"items"`, giá trị là object `{<kind>: <số nguyên >= 0>}`.
- **Nguyên liệu hợp lệ v1.1:** `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, `ca_keo`, `keo_neo`.
- Hai nguyên liệu sáng tạo `ca_ro_dong`, `rau_muong` được hỗ trợ tùy chọn trong headless mở rộng.
- **Quy tắc đọc/ghi:**
  - Khi ghi (`chonoi/inventory.py`): loại bỏ mục có số lượng `0`, sắp khóa theo thứ tự bảng chữ cái, ghi nguyên tử qua file tạm.
  - Chỉ ghi **đúng 1 lần** khi `gather` kết thúc (`gather_end`). Nếu dừng do `tick_limit` thì **không ghi** file đích. Nếu kết thúc với `reason="fainted"` thì giỏ rỗng (`{"items":{}}`).
  - Lỗi schema / nguyên liệu lạ / số âm / truyền đồng thời `--inventory` và `scenario.quan.stock` → thoát với mã **`2`** trước khi ghi output.

---

## 2. Giao diện giữa `sim/*` và `client/ui`

- **Nguyên tắc:** `client/ui` (`chonoi/web/index.html` qua `chonoi/live.py`) **chỉ đọc snapshot**, không chứa logic mô phỏng. Mọi mở rộng sáng tạo (ví dụ `--extra-content`) mặc định **tắt ở chế độ headless**.

### Dữ liệu UI đọc (từ `Session.snapshot()`)
- **Trường chung:** `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`"playing"` | `"finished"`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
- **Chế độ `gather`:**
  - `player`: `pos` (`[x, d]`), `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`.
  - `hold` (mảng theo thứ tự nhặt, LIFO), `hold_count`, `hold_capacity`.
  - `nodes[]`: `id`, `pos`, `kind`, `ready`, `regrow_ticks` (sắp bằng `sort_by_id`).
  - `fish[]`: `id`, `pos`, `kind`, `heading_deg` (sắp bằng `sort_by_id`).
- **Chế độ `quan`:**
  - `player`: `pos` (`[x, z]`).
  - `stock` (`{kind: count > 0}`), `hand` (tên món đang bưng hoặc `null`).
  - `stoves[]`: `id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`.
  - `tables[]`: `id`, `pos`, `customer_id`.
  - `customers[]` (sắp bằng `sort_by_id`).

### Lệnh UI gửi vào `sim` (`InputState` / `POST /input`)
- `move`: `[x, d]` ở `gather` (`d > 0` là bơi xuống) hoặc `[x, z]` ở `quan`; mỗi thành phần thuộc `[-1, 1]`, tự chuẩn hóa độ dài `<= 1`.
- Nút bấm v1.0 (`BUTTONS_V10`, xử lý theo cạnh lên `false -> true`):
  - `interact`: cập bến / hái nút (`gather`), tương tác bếp / bàn (`quan`).
  - `catch`: bắt đàn cá dưới nước (`gather`).

---

## 3. Danh sách sự kiện (`type: "event"`)

Mỗi dòng sự kiện có dạng: `{"type":"event","tick":<int>,"phase":"gather"|"quan","name":<str>,"data":{...}}`.

### Chế độ `gather` (phát: `GatherSim` · nghe: `runner`, `live`/UI, QA)
| Tên sự kiện | Trạng thái | `data` / Ghi chú |
|---|---|---|
| `node_regrown` | Đã có trong khung | `{"node_id": <id>}` |
| `gather_end` | Đã có trong khung | `{"reason": "docked"\|"time"\|"fainted", "inventory": {"items": {...}}}` |
| `dive`, `surface` | Lát 1 (`capkhai`) | `{"pos": [x, d]}` *(xác nhận chi tiết theo PRD-0 — `docs/clarify.md` #4)* |
| `oxygen_empty`, `choke`, `faint` | Lát 1 (`capkhai`) | Chốt khóa `data` theo PRD-0 (`docs/clarify.md` #3, #4) |
| `gather`, `fish_caught`, `hold_full` | Lát 2 (`capkhai`) | Chốt khóa `data` theo PRD-0 (`docs/clarify.md` #1, #4) |

### Chế độ `quan` (phát: `QuanSim` · nghe: `runner`, `live`/UI, QA)
| Tên sự kiện | Trạng thái | `data` / Ghi chú |
|---|---|---|
| `quan_end` | Đã có trong khung | `{"reason": "time", "money": ..., "earned": ..., "shift_earned": ..., "reputation": ...}` |
<<<<<<< HEAD
| `customer_arrived`, `customer_left`, `no_dish` | Lát 3 (`nhungvo631-stack`) | `customer_arrived`: `order_id`, `table_id`, `dish_id`, `reserved`; `customer_left`: `order_id`, `table_id`, `reason`, `reputation`; `no_dish`: `{}` (khi có bàn trống nhưng không còn món đủ kho). |
| `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | Lát 4 (`chur04`) | `cook_started`/`dish_ready`/`dish_picked`: `stove_id`, `order_id`, `dish_id` (`cook_started` thêm `items`, `base_price`); `served`: `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip`; `paid`: `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason`. |
=======
| `customer_arrived`, `customer_left`, `no_dish` | Lát 3 (`nhungvo631-stack`) | `customer_arrived`: `customer_id`, `table_id`, `dish`, `reserved`; `customer_left`: `customer_id`, `table_id`, `reserved`, `reputation`; `no_dish`: `reason` (`no_cookable_dish` hoặc `no_free_table`). |
| `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | Lát 4 (`chur04`) | Chốt khóa `data` theo PRD-0 mục E, F (`docs/clarify.md` #6, #7) |
| `fish_spawned` | Lát 1 (`capkhai`) | Cá sinh theo lịch, payload chốt theo PRD-2. |
| `monster_hit`, `faint` | Lát 2 (`nhungvo631-stack`) | `monster_hit`: `monster_id`, `damage`, `hp`, `removed`, `removed_count`, `invuln_ticks`; `faint`: `cause="monster"`, `pos`, `monster_id`. |
>>>>>>> 50867dc (Update code)
