# Hợp đồng tích hợp — Test Contract v1.1 (Phase 2)

> Mục 1–4 chốt lúc kickoff Phase 1 (v1.0), vẫn hiệu lực ở v1.1. Mục 5 thêm ở Phase 2. Người giữ: Integrator (nglngnguyen-gh). Đổi hợp đồng phải báo cả nhóm và ghi lý do trong `docs/adr/`.
> Nguồn: PRD-0 mục D, E, G. Phần cài đặt: `chonoi/inventory.py`, `chonoi/runner.py`, `chonoi/live.py`.

## 1. File kho (Lặn & Hái → Mở Quán)

### Schema

```json
{"items": {"<kind>": <int ≥ 0>, ...}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items`. Khóa gốc khác → mã 2. |
| `kind` | v1.1: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo` (`chonoi/inventory.py` `KINDS`). Kind lạ → mã 2. |
| Số lượng | Số nguyên không âm (không nhận `bool`, số thực, số âm → mã 2). Kind vắng tính là 0. |
| Bên ghi | Bỏ khóa có lượng 0, sắp khóa theo mã Unicode, JSON gọn (`,` `:`), một dòng, kết thúc `\n`, UTF-8. Kho rỗng là `{"items":{}}`. |
| Trần | Trần giỏ (`hold_capacity`) không áp lên kho quán. |

### Ai ghi, khi nào (lát 2 — `gather`)

- Chỉ `gather --inventory-out <file>` ghi, và ghi **đúng một lần** khi có `gather_end`.
- Nội dung file **giống hệt** `gather_end.data.inventory`.
- `reason`:
  - `docked` / `time`: kho là phần còn trong giỏ.
  - `fainted`: kho rỗng `{"items":{}}`.
- Chạm `--ticks` trước khi buổi sáng kết thúc: **không tạo, không ghi đè** file.
- Ghi file tạm cùng thư mục rồi thay thế nguyên tử (`write_inventory`).

### Ai đọc (lát 3, 4 — `quan`)

- `quan --inventory <file>` nạp thành `stock` (gồm cả phần giữ chỗ).
- Khai cả `--inventory` và `scenario.quan.stock` → mã 2.
- Thiếu cả hai → kho rỗng. Tiền và `earned` đầu lượt bằng 0.
- Kho khả dụng để chọn món = tồn vật lý − tổng `reserved` của các đơn.

### Ví dụ hợp lệ

- [`inventory.sample.json`](inventory.sample.json) (v1.2, kho cá thể, có một cá thể đã ươn `fresh` 29.5)
- [`inventory.sample.v11.json`](inventory.sample.v11.json) (v1.1, kho đếm — v1.2 trả mã 2): `{"items":{"bong_sung":2,"ca_loc":1}}`
- Kho rỗng: `{"items":{}}`

Ví dụ **không hợp lệ** (mã 2): `{"items":{"ca_loc":-1}}`, `{"items":{"ca_tra":1}}`, `{"items":{"ca_loc":1.5}}`, `{"items":{}, "money":0}`.

### Smoke hai tiến trình (AC-P1-50)

```bash
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json \
  --ticks 600 --out g.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory kho.json --ticks 0 --out q.jsonl
```

Kỳ vọng: `kho.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`, snapshot quán ở tick 0 có `"stock":{"bong_sung":2,"ca_loc":1}`.

## 2. Giao diện `sim/*` ↔ runner ↔ `client/ui`

```
sim = GatherSim | QuanSim(tuning, scenario, streams, ids[, inventory])
events = sim.step(inp)   # một tick; trả list (name, data)
sim.snapshot()           # trường riêng của mode (mục 4)
sim.done, sim.reason, sim.time_left_ticks, sim.money, sim.earned, sim.reputation
```

- **Runner** lo `tick`, `sim_tick`, `phase_tick`, thứ tự ghi event → snapshot, dòng `end`, điểm.
- **UI (`chonoi.live`)** chỉ **đọc**: `GET /state` trả snapshot + `meta` + `events`. UI **gửi vào** duy nhất `POST /input` `{"move":[a,b],"interact":bool,"catch":bool}`. UI không sửa trạng thái sim.
- Đồ họa, âm thanh, RNG giao diện nằm ngoài sim; headless không chạy UI.

## 3. Sự kiện

`data` đúng tên và thứ tự trường như dưới. Mảng `items`, `lost` là mảng `kind`.

### `gather` (lát 1, 2)

| `name` | `data` | Phát bởi |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển; chỉ khi đổi phía `d = surface_depth` | lát 1 |
| `oxygen_empty` | `oxygen_ticks: 0`, khi từ dương xuống 0 | lát 1 |
| `choke` | `hp` sau khi trừ | lát 1 |
| `faint` | `cause: "choke"`, `lost` (LIFO: nhặt sau bỏ trước), `hp: 0` | lát 1 |
| `gather` | `node_id`, `kind`, `amount` | lát 2 |
| `node_regrown` | `node_id` | lát 2 (đếm ngược đã có) |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | lát 2 |
| `fish_caught` | `fish_id`, `kind`, `yield` | lát 2 |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` (object mục 1) | lát 1 (`fainted`), lát 2 (`docked`, `time`) |

### `quan` (lát 3, 4)

| `name` | `data` | Phát bởi |
|---|---|---|
| `customer_arrived` | `order_id`, `table_id`, `dish_id` | lát 3 |
| `no_dish` | `{}` (có bàn nhưng thiếu món) | lát 3 |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`/`closing`), `reputation` | lát 3 |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (sắp theo kind), `base_price` | lát 4 |
| `dish_ready` / `dish_picked` | `stove_id`, `order_id`, `dish_id` | lát 4 |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | lát 4 |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) | lát 4 |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation` | lát 4 (khung đã có) |

## 4. Trạng thái chia sẻ giữa lát 3 và lát 4

Hai lát cùng sửa `chonoi/sim/quan.py`; thống nhất cấu trúc sau để làm song song bằng fixture.

**Khách** (lát 3 tạo, lát 4 cập nhật):

```json
{"id":"C1","table_id":"T1","dish_id":"goi_bong_sung","order_tick":120,
 "state":"waiting","patience_ticks_left":3600,"eat_ticks_left":0,
 "order_status":"reserved","reserved":{"bong_sung":2},"base_price":0,"tip":0}
```

- `state`: `waiting` → `eating`.
- `order_status`:
  - `reserved`: lát 3 đặt khi gọi món, giữ đúng công thức.
  - `assigned`: lát 4 đặt khi bắt đầu nấu, `reserved` thành `{}`, món ở bếp hoặc trên tay.
  - `served`: lát 4 đặt khi giao món.
  - `unfulfillable`: còn chờ, `reserved` rỗng, không có món.
- `id` khách cấp bằng `IdAllocator` (tiền tố `C`); `order_id` = id khách.

**Payload món** (bếp `dish`, `hand`): `{"order_id":"C1","dish_id":"goi_bong_sung","base_price":40}`.

**Bếp**: `{"id":"B1","pos":[2,8],"state":"idle|cooking|ready","dish":<payload|null>,"cook_ticks_left":int,"ready_ticks":int}`.

**Hàm dùng chung** (lát 3 viết, lát 4 gọi): `_release(customer)` nhả phần giữ, bỏ món của đơn ở bếp hoặc trên tay khi khách rời.

## 5. Thay đổi ở v1.1 (Phase 2, TICKET-02)

> Nguồn: TICKET-02 mục 1, 2, 4. Dữ liệu ở `game.contract.json` (`contract_version: "1.1"`), kiểm ở `chonoi/contract.py`.

### 5.1. Dữ liệu mới trong `game.contract.json`

| Khối | Thay đổi | Lát dùng |
|---|---|---|
| `gather.nodes` | Thêm N5 [76,0], N6 [90,0] `keo_neo` | lát 1 (Long) |
| `gather.fish_*` | `fish_initial` là **số 8** (không còn là danh sách); thêm `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x`, `fish_depths`, `fish_spawn_x`, `fish_spawn_depths`, `fish_weights`; `fish_yield.ca_keo = 2` | lát 1 (Long) |
| `gather.monsters` | `species.ca_sau`, `spawns` M1 (từ Ngày 1), M2 (từ Ngày 3), `invuln_ticks: 90`, `loss_ratio: 0.5` | lát 2 (Ly) |
| `quan` | Bếp B1, B2; bàn T1–T4 | lát 3 (Triết, Lên) |
| `menu` | Thêm `canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam` (tổng 6 món) | lát 3 |
| `day_plan` | 5 object `{day, dishes, ingredients}`; `contract.py` kiểm `ingredients` = tổng công thức × số suất | lát 4 (Nguyên) |
| `shop` | `max_ticks: 600`, `upgrades.oxygen[]`, `upgrades.hp[]` | lát 4 |
| `extensions` | Mảng mã mở rộng đã bật ở gốc manifest; hiện `[]` | ai làm mở rộng |

Quy ước nhóm cho khóa đề không ghi rõ (xem `docs/clarify.md` #10–12):
- `recoil_dist: 2.0` là **tổng** quãng lùi trong `recoil_ticks` (mỗi bước 2/60 m).
- Ngưỡng độ sâu phát hiện/chạm của quái = cận dưới `depths` của loài (Cá Sấu 10, Rắn 8).

### 5.2. Hàm dùng chung đã có trên nhánh `contract-v1.1`

- `GatherSim._spawn_school()` (`chonoi/sim/gather.py`): sinh một đàn theo luật "Sinh cá" (trọng số loài chuẩn hóa trên loài còn điểm, điểm cách mọi đàn > `fish_spawn_clearance`, hướng đều [0, 360), luồng RNG `fish_spawn`, id `F` tiếp nối). Đã dùng cho 8 đàn đầu ca; lát 1 gọi lại cho lịch `phase_tick = 360·k`.
- `contract.recipe_sum(dishes, menu)`: tổng nguyên liệu của kế hoạch, dùng cho `day_plan` và HUD "đã lấy / cần".
- Đàn cá có thêm `age_ticks` (scenario + snapshot).

### 5.3. Giao diện chuyển pha (`--mode day`, lát 4)

```
DayIntro → gather → EveningIntro → quan → DayResult → Shop → DayIntro … (Summary sau Ngày 5)
```

- **Runner `day`** giữ trạng thái xuyên Ngày: `day`, `money`, `earned`, `reputation`, `upgrades` (đã mua), `active_upgrades` (đang áp dụng), `days_completed`.
- **Dựng gather mỗi Ngày:** `GatherSim(tuning_ngày, scenario.gather, …)` với `oxygen_max_s`/`hp_max` lấy theo `active_upgrades`, quái lọc theo `from_day ≤ day`.
- **Bàn giao gather → quán:** trong bộ nhớ, đúng object `gather_end.data.inventory` (schema mục 1). Ngất → `{"items":{}}`, quán vẫn mở.
- **Dựng quán:** `QuanSim(tuning_ngày, …, inventory=kho)`; `tuning_ngày.menu` đã lọc còn id món trong `day_plan[day].dishes` (lọc trước nguyên liệu). Runner gán `money`/`earned`/`reputation` vào sim sau khi dựng và đọc lại khi pha xong. Cài ở `chonoi/day.py`.
- **Shop:** `money` trừ khi `bought`, `earned` giữ nguyên. Cấp mua hôm nay chỉ chép sang `active_upgrades` khi dựng Ngày kế.
- **Mọi sim** cần thêm: nhận `money`/`earned`/`reputation` ban đầu từ runner, và tôn trọng `pause` (runner không gọi `step` khi đang pause).

### 5.4. Sự kiện mới

| `name` | `data` | Phát bởi |
|---|---|---|
| `fish_spawned` | `id`, `kind`, `pos` (chỉ khi sinh theo lịch) | lát 1 |
| `monster_hit` | `monster_id`, `hp`, `lost` (LIFO), `pos` (người chơi) | lát 2 |
| `faint` | thêm `cause: "monster"`; `lost` = phần giỏ còn lại | lát 2 |
| `day_start`, `phase_start` | `{}` | lát 4 |
| `day_plan` | `dishes`, `ingredients` của Ngày | lát 4 |
| `paused`, `resumed` | `{}` | lát 4 |
| `bought` | `upgrade`, `level`, `price`, `money` | lát 4 |
| `buy_failed` | `action`, `reason` (`funds`/`max_level`/`out_of_stock`/`unknown`) | lát 4 |
| `shop_end` | `reason` (`done`/`time`) | lát 4 |
| `dish_burnt` | `stove_id`, `order_id`, `dish_id`, `order_status` (nếu bật burn) | mở rộng |

Trong `day`, vỏ mọi event có thêm `day`; snapshot mọi pha có `day`, `day_plan`, `upgrades`, `active_upgrades`. Dòng `end` thêm `days_completed`; đủ Ngày → `reason: "days_complete"`.

### 5.5. Inputs mới

Nút boolean `pause` (cả 3 mode), `shop_done` (Shop); `buy` là chuỗi (`oxygen`, `hp`, …) chỉ chạy ở frame khai báo. `chonoi/inputs.py` hiện chỉ nhận `interact`, `catch` (`BUTTONS_V10`) → lát 4 mở rộng danh sách nút và kiểu `buy`.

## 6. Thay đổi ở v1.2 (Phase 3, TICKET-03) — kho cá thể + độ tươi

> Kế hoạch, tác động, thứ tự tích hợp: `docs/plan/phase-3.md`. Breaking change + cách sửa fixture: `CHANGELOG.md`.

- **Cá thể nội bộ:** `{"id", "kind", "fresh_units"}` (`chonoi/items.py`); 240 đơn vị = 1 điểm tươi. Xuất ra ngoài bằng `items.public()` / `public_list()` → `{"id", "kind", "fresh"}`.
- **Bật v1.2:** `items.is_v12(tuning)` = manifest có `tuning.freshness`. Sim kiểm cờ này để chọn luật cá thể.
- **Hàm dùng chung:** `Freshness(tuning)` (hằng số/tick) · `ItemIds` (một đối tượng cho cả lượt, tăng xuyên pha và Ngày) · `new_item(ids, kind, fr)` · `decay(items, per_tick, fr)` → cá thể vừa ươn theo id · `pick_freshest(items, kind, n, fr, exclude)` · `price_by_fresh(giá, cá_thể_dùng)` · `lifo(items)`.
- **Sự kiện mới:** `spoiled {item_id, kind, location}` với `location` là `hold` (gather) hoặc `stock` (quán), phát đúng một lần, theo id.
- **Gather:** hao giỏ ở đầu bước (cùng hồi nút); hàng mới fresh 100, hao từ bước sau.
- **Quán:** hao kho thô (kể cả hàng giữ) → phát hết `spoiled` theo id → xử lý đơn có phần giữ vừa ươn (theo `order_tick` rồi id bàn): nhả toàn bộ, giữ lại đúng một lần, thiếu → `unfulfillable`. Món chín không hao.
- **`day`:** bàn giao mảng cá thể cùng tick, không hao thêm; `ItemIds` dùng chung cả lượt; Shop giữ `stock` không hao.
