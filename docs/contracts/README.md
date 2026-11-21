# Hợp đồng tích hợp (nhóm NgheAn)

Người giữ file này: Võ Hồng Lương (Integrator). Đổi hợp đồng thì báo cả nhóm trong kênh chung và ghi lý do ở cuối file (mục "Lịch sử đổi").
Nguồn sự thật cho số liệu là `game.contract.json`. Luật chỉ đọc số từ đó.

## 1. Schema file kho

File kho do `gather` ghi một lần khi có `gather_end`, `quan` đọc khi mở quán.

```json
{"items": {"ca_loc": 1, "bong_sung": 2}}
```

- Khóa gốc duy nhất là `items`; thêm khóa khác thì bị từ chối (mã thoát 2).
- Khóa trong `items` chỉ được là `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Giá trị là số nguyên `>= 0`; mục bằng 0 không ghi ra file.
- Ghi qua file tạm rồi thay thế, khóa sắp theo thứ tự chữ cái, kết thúc bằng một dòng mới.
- Ngất (`gather_end` với `reason: "fainted"`) ghi kho rỗng `{"items": {}}`.
- Từ contract v1.1 (Phase 2) có thêm hai nguyên liệu `ca_keo` và `keo_neo`; schema file kho không đổi.
- Mẫu hợp lệ: `docs/contracts/inventory.sample.json`. Code: `chonoi/inventory.py`.

## 2. Giao diện giữa `sim/*` và `client/ui`

UI chỉ ĐỌC trạng thái và GỬI lệnh. UI không sửa trạng thái sim.

**UI đọc** (cùng một dạng với dòng `snapshot` của headless và `GET /state` của `chonoi.live`):

- Chung: `tick`, `mode` (`gather` hoặc `quan`), `state` (`playing` hoặc `finished`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
- `gather`: `player` (`pos` `[x, d]`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `catch_cd_ticks`, `at_surface`), `hold` (mảng, cuối mảng là món mới nhặt), `hold_count`, `hold_capacity`, `nodes` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish` (`id`, `pos`, `kind`, `heading_deg`). Từ v1.1 (P2-04): `player.invuln_ticks` và `monsters` (`id`, `kind`, `pos`, `state` là `patrol`, `chase` hoặc `recoil`, `waypoint_index`, `recoil_ticks_left`).
- `quan`: `player` (`pos` `[x, z]`), `stock`, `hand` (`null` hoặc payload món `{order_id, dish_id, base_price}`), `stoves` (`id`, `pos`, `state` là `idle`, `cooking` hoặc `ready`, `dish` là `null` hoặc payload món, `cook_ticks_left`, `ready_ticks`), `tables` (`id`, `pos`, `customer_id`, `null` khi trống), `customers` (chỉ khách còn ngồi: `id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip`).
- Trường nào chưa có thì UI bỏ qua, không báo lỗi. Sim thêm trường mới thì không được đổi tên hoặc ý nghĩa trường cũ.
- Riêng cửa sổ `chonoi.live` (không có trong JSONL headless): `GET /state` trả thêm `meta` (tuning của chế độ đang chạy), `events` (tối đa 40 sự kiện gần nhất), `finished` (bool) và `error` (chuỗi lỗi luật hoặc `null`); `POST /input` nhận `{"move": [a, b], "interact": bool, "catch": bool}` (sai thì HTTP 400); `POST /restart` chơi lại cùng seed và scenario.
- Từ P2-08 (v1.1): `POST /input` nhận thêm `pause`, `shop_done` (bool) và `buy` (chuỗi, một lần). Chạy `chonoi.live` không có `--mode` thì mở menu: `GET /state` trả `{"screen": "menu", "modes", "days_max", "seed"}`, `POST /start {"mode", "days"}` vào chơi, `POST /menu` về menu. Khi chơi, `GET /state` có thêm `screen: "game"`, `fixed_mode`, `days_total` (chỉ day); `meta` là tuning của pha đang chạy (`gather`, `quan` hoặc `shop`). UI chọn cảnh theo `phase` (rồi mới tới `mode`) và vẽ màn tạm dừng khi `state` là `paused`.

**UI gửi** (qua `chonoi.inputs.InputState`, mỗi tick một lần):

- `move`: vector 2 chiều. `gather` là `[x, d]` (thành phần thứ hai dương là bơi xuống); `quan` là `[x, z]`.
- `interact` (phím E): cập bến, hái nút, thao tác bếp và bàn.
- `catch` (phím Space): bắt cá, chỉ có ở `gather`.

Quy ước thêm: mọi số ngẫu nhiên qua `Streams`; không dùng đồng hồ hệ thống; id sắp bằng `ids.sort_by_id`.

## 3. Danh sách sự kiện

Mỗi sự kiện là một dòng JSONL `{"type":"event","tick":…,"phase":…,"name":…,"data":{…}}`. "Phát" là module sinh sự kiện, "Nghe" là module đọc nó.

| Sự kiện | Chế độ | `data` | Phát | Nghe |
|---|---|---|---|---|
| `dive` | gather | `pos` lúc lặn | `sim/gather` | UI |
| `surface` | gather | `pos` lúc nổi | `sim/gather` | UI |
| `oxygen_empty` | gather | `oxygen_ticks` (luôn 0) | `sim/gather` | UI |
| `choke` | gather | `hp` còn lại | `sim/gather` | UI |
| `faint` | gather | `cause` (`choke`, hoặc `monster` từ v1.1), `lost` (món rơi, mới nhặt trước), `hp` (0) | `sim/gather` | UI, QA |
| `monster_hit` | gather (v1.1) | `monster_id`, `kind`, `hp` còn lại, `lost` (món rơi do cắn, mới nhặt trước) | `sim/monsters` | UI, QA |
| `gather` | gather | `node_id`, `kind`, `amount` | `sim/gather` | UI, QA |
| `hold_full` | gather | `action` (`gather` hoặc `catch`), `node_id` hoặc `fish_id`, `required`, `free` | `sim/gather` | UI |
| `fish_caught` | gather | `fish_id`, `kind`, `yield` | `sim/gather` | UI, QA |
| `node_regrown` | gather | `node_id` | `sim/gather` (khung đã có) | UI |
| `gather_end` | gather | `reason` (`docked`, `fainted`, `time`), `inventory.items` | `sim/gather` (khung đã có) | `sim/quan`, QA |
| `customer_arrived` | quan | `order_id`, `table_id`, `dish_id` | `sim/quan` | UI, QA |
| `no_dish` | quan | `{}` (khi có bàn trống mà không có món đủ nguyên liệu) | `sim/quan` | UI, QA |
| `cook_started` | quan | `stove_id`, `order_id`, `dish_id`, `items`, `base_price` | `sim/quan` | UI |
| `dish_ready` | quan | `stove_id`, `order_id`, `dish_id` | `sim/quan` | UI |
| `dish_picked` | quan | `stove_id`, `order_id`, `dish_id` | `sim/quan` | UI |
| `served` | quan | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | `sim/quan` | UI, QA |
| `paid` | quan | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating` hoặc `closing`) | `sim/quan` | UI, QA |
| `customer_left` | quan | `order_id`, `table_id`, `reason` (`patience` hoặc `closing`), `reputation` | `sim/quan` | UI, QA |
| `quan_end` | quan | `reason` (`time`), `money`, `earned`, `shift_earned`, `reputation` | `sim/quan` (khung đã có) | QA |

Các sự kiện `gather` (từ `dive` đến `gather_end`) khớp code của P1-04 và P1-05 (PR #5) và PRD-0 mục E. Các sự kiện `quan` theo PRD-0 mục E (đối chiếu trên lab board); `order_id` bằng id khách. Khi code của B (P1-06, P1-07) khác bảng này thì sửa code hoặc ghi lý do ở đây.

## Lịch sử đổi

- Bản đầu do Integrator viết ở nhánh `p1-01-03-kickoff`, cần A, B, C đọc và đồng ý trước khi viết luật.
- Cập nhật bảng sự kiện `gather` và bỏ `invuln_ticks` khỏi snapshot theo code của P1-04 và P1-05 (v1.0 không có `invuln_ticks`). Phase 2 (v1.1) thêm lại `invuln_ticks`, `attack_cd_ticks`, `monsters[]` và các sự kiện `monster_hit`, `fish_spawned`, `day_start`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`; cần quyết định chấp nhận hay từ chối `invuln_ticks` theo `contract_version`.
- Bảng sự kiện `quan` và `customer_arrived` viết lại theo PRD-0 mục E (bản đề xuất cũ dùng `customer_id` và thiếu `customer_arrived`).
- P2-04 (C): thêm `monster_hit`, `faint.cause = monster`, `player.invuln_ticks` và `monsters[]` trong snapshot gather v1.1; scenario gather nhận `monsters` (thay bố trí mặc định) và `player.invuln_ticks` (chỉ v1.1).
