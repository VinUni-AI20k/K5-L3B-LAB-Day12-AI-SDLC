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
- **Kho cá thể (contract 1.2, Ticket-03):** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`. `items` là mảng theo thứ tự vào kho (mất hàng theo LIFO dùng thứ tự này), `id` dạng `I<n>` không trùng, `fresh` là điểm tươi trong `[0, fresh_max]` (làm tròn 3 chữ số). Ở 1.2 file kho dạng đếm thì mã 2; ở 1.0 và 1.1 file kho dạng cá thể thì mã 2. Mẫu: `docs/contracts/inventory.v12.sample.json`. Code: `read_inventory_for`, `validate_individuals`, adapter `counts_to_individuals` và `individuals_to_counts`; độ tươi số nguyên đơn vị ở `chonoi/freshness.py`. `game.contract.json` có sẵn `tuning.freshness` nhưng `contract_version` vẫn "1.1" đến P3-08.

## 2. Giao diện giữa `sim/*` và `client/ui`

UI chỉ ĐỌC trạng thái và GỬI lệnh. UI không sửa trạng thái sim.

**UI đọc** (cùng một dạng với dòng `snapshot` của headless và `GET /state` của `chonoi.live`):

- Chung: `tick`, `mode` (`gather` hoặc `quan`), `state` (`playing` hoặc `finished`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`. Từ v1.1: `mode` thêm `day`, `state` thêm `paused`, và `sim_tick` (số bước gameplay đã chạy; `tick` ngoài vẫn tăng lúc pause), `phase`, `phase_tick` (số bước từ khi pha hiện tại bắt đầu).
- `gather`: `player` (`pos` `[x, d]`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `catch_cd_ticks`, `at_surface`), `hold` (mảng, cuối mảng là món mới nhặt), `hold_count`, `hold_capacity`, `nodes` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish` (`id`, `pos`, `kind`, `heading_deg`). Từ v1.1 (P2-04): `player.invuln_ticks` và `monsters` (`id`, `kind`, `pos`, `state` là `patrol`, `chase` hoặc `recoil`, `waypoint_index`, `recoil_ticks_left`).
- `quan`: `player` (`pos` `[x, z]`), `stock`, `hand` (`null` hoặc payload món `{order_id, dish_id, base_price}`), `stoves` (`id`, `pos`, `state` là `idle`, `cooking` hoặc `ready`, `dish` là `null` hoặc payload món, `cook_ticks_left`, `ready_ticks`), `tables` (`id`, `pos`, `customer_id`, `null` khi trống), `customers` (chỉ khách còn ngồi: `id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip`).
- `day` (v1.1, P2-07): snapshot của pha đang chạy (`gather`, `quan` hoặc `shop`) cộng `day` (số Ngày, từ 1), `day_plan` (`{dishes, ingredients}` của Ngày), `upgrades` (cấp ĐÃ MUA, vừa mua hiện ngay) và `active_upgrades` (cấp ĐANG CÓ HIỆU LỰC của Ngày, cấp mới mua chỉ có hiệu lực từ Ngày sau). Pha `shop` có `money`, `earned`, `reputation`, `time_left_ticks`, `stock` (kho dư, chỉ để hiển thị) và `upgrades` (`oxygen`, `hp`). Snapshot gather v1.1 có `fish[].age_ticks`.
- Trường nào chưa có thì UI bỏ qua, không báo lỗi. Sim thêm trường mới thì không được đổi tên hoặc ý nghĩa trường cũ.
- Riêng cửa sổ `chonoi.live` (không có trong JSONL headless): `GET /state` trả thêm `meta` (tuning của chế độ đang chạy), `events` (tối đa 40 sự kiện gần nhất), `finished` (bool) và `error` (chuỗi lỗi luật hoặc `null`); `POST /input` nhận `{"move": [a, b], "interact": bool, "catch": bool}` (sai thì HTTP 400); `POST /restart` chơi lại cùng seed và scenario.
- Từ P2-08 (v1.1): `POST /input` nhận thêm `pause`, `shop_done` (bool) và `buy` (chuỗi, một lần). Chạy `chonoi.live` không có `--mode` thì mở menu: `GET /state` trả `{"screen": "menu", "modes", "days_max", "seed"}`, `POST /start {"mode", "days"}` vào chơi, `POST /menu` về menu. Khi chơi, `GET /state` có thêm `screen: "game"`, `fixed_mode`, `days_total` (chỉ day); `meta` là tuning của pha đang chạy (`gather`, `quan` hoặc `shop`). UI chọn cảnh theo `phase` (rồi mới tới `mode`) và vẽ màn tạm dừng khi `state` là `paused`.

**UI gửi** (qua `chonoi.inputs.InputState`, mỗi tick một lần):

- `move`: vector 2 chiều. `gather` là `[x, d]` (thành phần thứ hai dương là bơi xuống); `quan` là `[x, z]`.
- `interact` (phím E): cập bến, hái nút, thao tác bếp và bàn.
- `catch` (phím Space): bắt cá, chỉ có ở `gather`.
- Từ v1.1: `pause` (cạnh lên, cả ba chế độ; cạnh kế tiếp là tiếp tục), `shop_done` (cạnh lên, đóng Shop, chỉ ở pha `shop` của `day`), `buy` (chuỗi `oxygen` hoặc `hp`, chỉ có tác dụng ở đúng frame khai báo, không kế thừa sang frame sau; chỉ ở pha `shop`). `attack` và `photo` là phần mở rộng, chưa hỗ trợ.

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
| `fish_spawned` | gather (v1.1) | `id`, `kind`, `pos` | `sim/fish` | UI, QA |
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
| `day_start` | day (v1.1) | `{}` | `sim/day` | UI, QA |
| `day_plan` | day (v1.1) | `dishes`, `ingredients` của Ngày | `sim/day` | UI, QA |
| `phase_start` | day (v1.1) | `{}` (`phase` là `gather`, `quan` hoặc `shop`) | `sim/day` | UI, QA |
| `paused`, `resumed` | mọi chế độ (v1.1) | `{}` | `runner` | UI, QA |
| `bought` | day, pha shop (v1.1) | `upgrade`, `level`, `price`, `money` còn lại | `sim/shop` | UI, QA |
| `buy_failed` | day, pha shop (v1.1) | `action`, `reason` (`unknown`, `max_level` hoặc `funds`) | `sim/shop` | UI, QA |
| `shop_end` | day, pha shop (v1.1) | `reason` (`done` hoặc `time`) | `sim/shop` | UI, QA |

Chế độ `day`: mỗi dòng event có thêm khóa `day` (sau `phase`). Thứ tự chuyển pha trong một Ngày: `day_start`, `day_plan`, `phase_start` (gather) lúc tick 0; `gather_end` rồi `phase_start` (quan) cùng tick, kể cả khi ngất; `quan_end` rồi `phase_start` (shop) cùng tick; `shop_end` rồi `day_start` của Ngày kế cùng tick. Sự kiện kết thúc mang pha cũ. Dòng `end` của `day` thêm `days_completed`, `reason` là `days_complete` khi đủ `--days`.

Các sự kiện `gather` (từ `dive` đến `gather_end`) khớp code của P1-04 và P1-05 (PR #5) và PRD-0 mục E. Các sự kiện `quan` theo PRD-0 mục E (đối chiếu trên lab board); `order_id` bằng id khách. Khi code của B (P1-06, P1-07) khác bảng này thì sửa code hoặc ghi lý do ở đây.

## Lịch sử đổi

- Bản đầu do Integrator viết ở nhánh `p1-01-03-kickoff`, cần A, B, C đọc và đồng ý trước khi viết luật.
- Cập nhật bảng sự kiện `gather` và bỏ `invuln_ticks` khỏi snapshot theo code của P1-04 và P1-05 (v1.0 không có `invuln_ticks`). Phase 2 (v1.1) thêm lại `invuln_ticks`, `attack_cd_ticks`, `monsters[]` và các sự kiện `monster_hit`, `fish_spawned`, `day_start`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`; cần quyết định chấp nhận hay từ chối `invuln_ticks` theo `contract_version`.
- Bảng sự kiện `quan` và `customer_arrived` viết lại theo PRD-0 mục E (bản đề xuất cũ dùng `customer_id` và thiếu `customer_arrived`).
- P2-11 (D): thêm vào bảng v1.1 các phần P2-03, P2-06, P2-07 đã có trong code: `fish_spawned` và `fish[].age_ticks`; chế độ `day` (snapshot `day`, `day_plan`, `upgrades`, `active_upgrades`, thứ tự pha, `days_completed`); input `pause`, `shop_done`, `buy`; sự kiện `day_start`, `day_plan`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`. Chỉ thêm, không đổi tên hay nghĩa trường cũ.
- P2-04 (C): thêm `monster_hit`, `faint.cause = monster`, `player.invuln_ticks` và `monsters[]` trong snapshot gather v1.1; scenario gather nhận `monsters` (thay bố trí mặc định) và `player.invuln_ticks` (chỉ v1.1).
- P3-02 (D): thêm kho cá thể (schema, adapter, đọc theo `contract_version`), khối `tuning.freshness` và `chonoi/freshness.py`. Chỉ thêm; `contract_version` chưa đổi nên hành vi v1.1 giữ nguyên.
