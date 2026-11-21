# Hợp đồng tích hợp — Nhóm Nicecentt (Contract v1.0)

> Người giữ hợp đồng (Integrator): **Võ Thị Phương Nhung (`nhungvo631-stack`)**.
> Khi cần đổi hợp đồng (schema kho, snapshot, tên sự kiện, `game.contract.json`): báo cả nhóm trước và ghi lại lý do trong `docs/adr/` hoặc `docs/clarify.md`.

---

## 1. Schema file kho (Contract G)

- **File mẫu hợp lệ:** [`inventory.sample.json`](./inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`
- **Cấu trúc bắt buộc:** đúng 1 khóa gốc `"items"`, giá trị là object `{<kind>: <số nguyên >= 0>}`.
- **Nguyên liệu hợp lệ (v1.0 / `KINDS_P1`):** `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
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
| `customer_left`, `no_dish` *(và sự kiện khách đến theo PRD-0)* | Lát 3 (`nhungvo631-stack`) | Chốt tên & `data` theo PRD-0 mục E, F (`docs/clarify.md` #5) |
| `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | Lát 4 (`chur04`) | Chốt khóa `data` theo PRD-0 mục E, F (`docs/clarify.md` #6, #7) |
