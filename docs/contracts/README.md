# Hợp đồng tích hợp (Test Contract v1.1)

Người giữ: Integrator. Muốn đổi tên sự kiện, trường `data`, schema kho, cấu trúc khách hay hàm dựng sim thì báo cả nhóm trước, rồi ghi ADR trong `docs/adr/`, vì thay đổi ảnh hưởng nhiều lát và test ẩn.

Mục 1 đến 4 là hợp đồng Phase 1 (v1.0), vẫn còn hiệu lực. Mục 5 là phần thêm và đổi của v1.1 (Ticket-02).

## 1. File kho (PRD-0 mục G)

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Gốc chỉ có khóa `items`. Giá trị là object `kind -> số nguyên không âm`.
- `kind` thuộc 6 nguyên liệu v1.1: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo` (`chonoi.inventory.KINDS`). Kind vắng tính là 0, bên ghi bỏ khóa có lượng 0. Kho rỗng là `{"items":{}}`.
- Bên đọc (`quan --inventory`) từ chối sai schema, kind lạ, số âm hoặc không nguyên bằng mã thoát 2.
- `gather --inventory-out` ghi đúng một lần khi có `gather_end`, nội dung khớp `inventory` trong event đó. Ngất ghi kho rỗng. Chạm `--ticks` trước khi kết thúc buổi thì không tạo và không ghi đè file.
- Ghi qua file tạm cùng thư mục rồi thay thế nguyên tử (`chonoi/inventory.py`).
- Trần giỏ không áp lên kho quán.
- File mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json).

Smoke hai tiến trình:

```bash
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Snapshot quán ở tick 0 phải có `"stock":{"bong_sung":2,"ca_loc":1}`.

## 2. Danh sách sự kiện (PRD-0 mục E)

Event là dòng `{"type":"event","tick":k+1,"phase":...,"name":...,"data":{...}}`, ghi theo thứ tự xử lý trong bước, trước snapshot của tick đó. `items` và `lost` là mảng kind.

### Gather

| Sự kiện | `data` | Ai phát (hàm) |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển, chỉ khi đổi phía biên mặt nước (`d <= surface_depth` là mặt nước) | A, `_dive_surface` |
| `oxygen_empty` | `oxygen_ticks: 0`, khi oxy từ dương xuống 0 | A, `_oxygen_and_choke` |
| `choke` | `hp` sau khi trừ | A, `_oxygen_and_choke` |
| `faint` | `cause: "choke"`, `lost` (giỏ theo thứ tự bỏ, nhặt sau bỏ trước), `hp: 0` | A, `_oxygen_and_choke` |
| `gather` | `node_id`, `kind`, `amount` | B, `_try_harvest` |
| `node_regrown` | `node_id` | khung (`step`, bước 1) |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | B |
| `fish_caught` | `fish_id`, `kind`, `yield` | B, `_try_catch` |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` theo mục 1 | khung (`_finish`) |

Thứ tự trong một bước gather: `node_regrown` → `dive`/`surface` → `oxygen_empty` → `choke` → `faint` + `gather_end(fainted)` (dừng) → `gather_end(docked)` hoặc `gather`/`hold_full` → `fish_caught`/`hold_full` → `gather_end(time)`.

### Quán

| Sự kiện | `data` | Ai phát |
|---|---|---|
| `customer_arrived` | `order_id`, `table_id`, `dish_id` | C, `_spawn_customer` |
| `no_dish` | `{}` khi có bàn trống mà không món nào đủ kho khả dụng | C, `_spawn_customer` |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`/`closing`), `reputation` | C, `_settle_customers` |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (sắp theo kind), `base_price` | D, `_interact` |
| `dish_ready` | `stove_id`, `order_id`, `dish_id` | D, `_stoves_ready` |
| `dish_picked` | `stove_id`, `order_id`, `dish_id` | D, `_interact` |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | D, `_interact` |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) | D, `_pay_customers` |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation` | khung (`step`) |

Thứ tự gọi trong `QuanSim.step` (đổi thì báo nhóm): `_tick_timers` → `_stoves_ready` → `_move` → `_interact(inp, events)` (D tự kiểm cạnh lên `interact`) → `_settle_customers(events)` (gọi `_pay_customers` của D trước, rồi xử lý khách chờ bỏ đi hoặc `closing`) → `_spawn_customer` (tự bỏ qua khi hết giờ) → `quan_end` nếu hết ca.

## 3. Dữ liệu khách dùng chung giữa lát 3 (C) và lát 4 (D)

Mỗi khách trong `QuanSim.customers` là một dict theo PRD-0 mục D:

| Trường | Kiểu | Ghi chú | Ai ghi |
|---|---|---|---|
| `id` | chuỗi | Cũng là `order_id`. Cấp bằng `self.ids.new("C")` | C |
| `table_id` | chuỗi | Bàn trống id nhỏ nhất | C |
| `dish_id` | chuỗi | Một trong 3 món | C |
| `order_tick` | số nguyên | `phase_tick` lúc khách đến | C |
| `state` | `waiting` / `eating` | | C tạo, D đổi sang `eating` |
| `patience_ticks_left` | số nguyên | Đầy = `patience_s * 60`, giảm từ bước sau khi đến | C |
| `eat_ticks_left` | số nguyên | `eat_s * 60` khi được phục vụ | D |
| `order_status` | `reserved` / `assigned` / `unfulfillable` / `served` | | C tạo `reserved`, D đổi |
| `reserved` | object kind → số | Đúng công thức món; rỗng sau khi bếp lấy | C tạo, D xóa khi nấu |
| `base_price` | số nguyên | Chốt khi `cook_started` | D |
| `tip` | số nguyên | `floor(base_price * tip_rate)` nếu tỷ lệ kiên nhẫn còn lại ≥ `tip_min_patience_ratio`, ngược lại 0 | D |

Món trên bếp hoặc trên tay là payload `{order_id, dish_id, base_price}`. Kho khả dụng = `stock` trừ tổng `reserved` của các khách (`QuanSim.available_stock()`). Khi khách rời (`_customer_leaves`): bỏ khách khỏi danh sách là nhả `reserved`, rồi gọi `self._drop_order(order_id)` để D bỏ món của đơn trên bếp hoặc trên tay. Nguyên liệu đã nấu không hoàn lại.

## 4. Giao diện mô phỏng với UI

- Headless và cửa sổ chơi dùng chung lớp sim qua `runner.Session`. UI không chứa luật.
- UI chỉ đọc snapshot qua `GET /state` (cùng trường với dòng snapshot của headless, thêm `meta` và `events` gần nhất).
- UI chỉ gửi phím qua `POST /input` `{"move":[a,b],"interact":bool,"catch":bool}` và `POST /restart`.
- Snapshot headless chỉ chứa trường theo PRD-0 mục E. Trường phục vụ riêng cho hiển thị thì tính ở client, ví dụ kho khả dụng.

## 5. Thêm và đổi ở v1.1 (Ticket-02)

### 5.1. Manifest

- `contract_version: "1.1"`. `extensions` ở gốc manifest là mảng mã mở rộng đang bật (`weapon`, `net`, `snake`, `burn`, `vendor`, `ca_ho`), hiện là `["snake"]` (Rắn Hổ Mây: `monsters.species.ran` + spawn M3, LeBao403). `contract.validate_extensions` kiểm mã khai khớp dữ liệu.
- Số chuẩn và dữ liệu theo Ticket-02 mục 1, 2: `gather.fish_initial` là số (8), các khóa cá bơi/sinh, `gather.monsters`, nút N5/N6 kèo nèo, `quan` có B1-B2 và T1-T4, 6 món, `day_plan` (5 Ngày, `ingredients` = tổng công thức × suất), `shop`.
- `chonoi/contract.py` kiểm toàn bộ khi nạp; sai thì mã 2. Hàm dùng chung: `plan_ingredients(menu, dishes)`, `upgrade_value(tuning, kind, level, base)`, `extensions(contract)`.

### 5.2. CLI, inputs, pause

- `--mode gather|quan|day`, `--days N` (chỉ với day, 1..5, mặc định 1). `--inventory`, `--inventory-out` vẫn chỉ cho hai mode độc lập.
- Nút boolean: `interact`, `catch`, `pause` (mọi mode), `shop_done` (Shop). Trường `buy`: chuỗi khác rỗng, chỉ có hiệu lực tại đúng frame khai báo (`InputState.buy`). Nút đúng kiểu nhưng sai pha thì sim bỏ qua.
- Pause ở `runner.PauseGate`, dùng chung mọi mode: cạnh `pause` xét trước; vào pause chỉ tăng `tick` ngoài và phát `paused`; trong pause bỏ qua hành động và `buy`, `sim_tick`, `phase_tick`, timer đứng yên; cạnh kế tiếp phát `resumed` và chạy gameplay ngay bước đó. Snapshot `state: "paused"`.
- `tick` là bước ngoài, `sim_tick` là bước gameplay, `phase_tick` lấy từ sim.

### 5.3. Hàm dựng sim (C dùng để ghép vòng ngày)

| Lớp | Chữ ký | Ghi chú |
|---|---|---|
| `GatherSim` | `(tuning, scenario, streams, ids, day=1, active_upgrades=None)` | `day` lọc quái theo `from_day`; `active_upgrades` quyết định `oxygen_max`, `hp_max` |
| `QuanSim` | `(tuning, scenario, streams, ids, inventory=None, plan_dishes=None, carry=None)` | `plan_dishes`: id món của kế hoạch (None = cả 6 món); `carry = {money, earned, reputation}` |
| `ShopSim` | `(tuning, stock, carry, upgrades)` | `chonoi/shop.py`, C viết |
| `DaySession` | `(tuning, scenario, seed, days, contract=None)` | `chonoi/day.py`, C viết, cùng giao diện với `runner.Session` |

- Cấp nâng cấp là map `{"oxygen": n, "hp": n}`. `upgrades` là cấp đã mua; `active_upgrades` là cấp đang áp dụng, chép từ `upgrades` lúc dựng Ngày mới.
- RNG: một `Streams(seed)` cho cả lượt. Luồng: `fish_init` (8 đàn đầu ca), `fish_turn`, `fish_spawn`, `customers`.

### 5.4. Gather

Thứ tự trong `GatherSim.step` (mục 4.5): đồng hồ, cooldown, bất tử, hồi nút → bơi → `dive`/`surface` → oxy, ngạt → `_update_monsters` (A) → bến, `_try_harvest` (B) → `_try_catch` (B, theo vị trí cá trước khi bơi) → hết giờ → nếu còn giờ và `random_fish`: `_fish_swim`, `_spawn_fish` (B).

- `random_fish: false`: không cá mặc định, không bơi, không sinh; cá fixture đứng yên. Khai `fish` khi cờ bật thì thay đàn ban đầu, vẫn bơi và sinh.
- Quái: mặc định từ `monsters.spawns` có `from_day <= day`; scenario `monsters[]` thay danh sách. Mỗi con `{id, kind, pos, waypoints, target_idx (mặc định 1), state (patrol|chase|recoil), state_ticks_left, recoil_dir}`.
- Snapshot gather thêm `monsters[]`, `fish[].age_ticks`; `player.hp_max` theo cấp.

### 5.5. Sự kiện mới

| Sự kiện | `data` | Ai phát |
|---|---|---|
| `monster_hit` | `monster_id`, `hp`, `lost` (LIFO), `pos` (người chơi) | A, `_update_monsters` (Cá Sấu và Rắn) |
| `faint` | thêm `cause: "monster"`; `lost` là phần giỏ còn lại; `hp: 0` | A |
| `fish_spawned` | `id`, `kind`, `pos` | B, `_spawn_fish` |
| `paused`, `resumed` | `{}` | runner (`PauseGate`) |
| `day_start`, `phase_start` | `{}` | C, `DaySession` |
| `day_plan` | `dishes`, `ingredients` | C |
| `bought` | `upgrade`, `level`, `price`, `money` | C, `ShopSim` |
| `buy_failed` | `action`, `reason` (`funds`/`max_level`/`out_of_stock`/`unknown`) | C |
| `shop_end` | `reason` (`done`/`time`) | C |
| `dish_burnt` (mở rộng Cháy) | `stove_id`, `order_id`, `dish_id`, `order_status` | D |

Trong day, vỏ event có thêm `day`; snapshot mọi pha có `day`, `day_plan`, `upgrades`, `active_upgrades`; dòng `end` thêm `days_completed`.

### 5.6. Giả định đang dùng (chờ xác nhận trong docs/clarify.md)

- 8 đàn đầu ca: lặp đúng luật sinh 8 lần (trọng số loài chuẩn hóa trên loài còn điểm, chọn đều điểm cách mọi đàn > 1 m, hướng đều trong [0, 360)), luồng `fish_init`.
- **Ghi chú sở hữu:** `GatherSim._pick_spawn` và `_initial_fish` do A (LeBao403) viết trong nền v1.1 để main xanh khi `fish_initial` đổi sang số 8. Đoạn này thuộc lát của B: B sở hữu (review, viết test cho cá, chỉnh lại sau khi có câu trả lời clarify) và dùng lại `_pick_spawn` khi nối lịch sinh trong `_spawn_fish`. Việc còn lại của B: cá bơi (`_fish_swim`), nối lịch sinh (`_spawn_fish`), test cá.
- `recoil_dist: 2.0` là tổng quãng lùi trong `recoil_ticks` (60) bước, tức 2/60 m mỗi bước.
- Ngưỡng độ sâu phát hiện và chạm của quái là `depths[0]` của loài.
- Nút `attack`, `photo` khi chưa bật mở rộng vẫn là trường lạ (mã 2) như smoke P1.
- `--mode day` tạm thời trả mã 2 cho tới khi `DaySession` (C) xong. `ShopSim` và phần kiểm giá trị khối `day` là khung cho C.
- Test cũ sửa theo luật v1.1 trong nền (A sửa, ghi lý do trong commit, chủ test review lại): `test_smoke_p1` (6 thành `fish_initial` = 8 đàn), `test_lat3_khach.test_het_ban_trong_thi_bo_luot` (4 bàn nên lấp đủ T1-T4), `test_lat4_quan.test_ngoai_ban_kinh_khong_lam_gi` (B2 ở [5, 8] nên đứng lệch theo trục z).

### 5.7. Quái (đã làm, LeBao403)

`GatherSim._update_monsters` viết theo loài, dùng chung cho Cá Sấu (`ca_sau`) và Rắn Hổ Mây (`ran`):

- Mỗi bước duyệt quái theo id. `recoil`: lùi `recoil_dist / recoil_ticks` mét theo `recoil_dir` rồi chặn; hết đếm thì về `patrol`, xét phát hiện và chạm từ bước kế. `patrol`/`chase`: đổi trạng thái theo người chơi (vào `chase` khi người chơi ở d >= `depths[0]` và cách <= `detect_radius`; về `patrol` khi cách > `exit_radius` hoặc người chơi lên d < `depths[0]`), rồi đi `patrol_speed` về waypoint (tới nơi đổi `target_idx` cho bước sau) hoặc `chase_speed` về phía người chơi. Chặn theo biên map và dải `depths` của loài.
- Sau khi cả hai đã di chuyển: tối đa một hit, con gần nhất (hòa id), không ở recoil, trong `hit_radius`, người chơi ở d >= `depths[0]` và `invuln_ticks == 0`. Hit: -1 Máu, bỏ `floor(len(hold) × loss_ratio)` theo LIFO, `invuln_ticks = 90`, `monster_hit`, con đó vào `recoil` 60 bước từ bước sau với hướng xa người chơi (trùng tâm dùng +x).
- Máu 0 do quái: `faint{cause: "monster", lost: phần giỏ còn lại theo LIFO, hp: 0}` rồi `gather_end(fainted)`. Ngạt xét trước quái trong cùng tick.

## 6. Thêm và đổi ở v1.2 (Ticket-03, kho cá thể và độ tươi)

Quyết định và thứ tự tích hợp: [`docs/adr/0001-kho-ca-the.md`](../adr/0001-kho-ca-the.md). Trong lúc chuyển, code chạy được cả 1.1 và 1.2; manifest bật 1.2 khi mọi lát đã sẵn sàng.

### 6.1. Manifest và đơn vị

- `contract_version: "1.2"` bắt buộc `tuning.freshness = {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`; 1.1 không được có khối này. Code chọn đường v1.2 bằng `chonoi.fresh.enabled(tuning)`.
- 240 đơn vị = 1 điểm tươi. Giỏ trừ 2 đơn vị/tick, kho quán trừ 1 đơn vị/tick, ươn khi `u < 7200`. Dùng `fresh.cfg(tuning)` để đọc các hằng số này.

### 6.2. Cá thể

- Trong code: `{"id": "I1", "kind": "ca_linh", "u": 24000}`. Ra ngoài: `{"id", "kind", "fresh"}` qua `fresh.public` / `fresh.public_list` / `fresh.out`.
- Helper (`chonoi/fresh.py`): `new_item(ids, kind, tuning)` (id `I<n>` nối tiếp, fresh 100), `from_public`, `is_spoiled`, `decay(items, units, tuning)` (trả cá thể vừa ươn, sắp theo id).
- Một `IdAllocator` cho cả lượt (day dùng chung qua các Ngày). Id trong fixture được `reserve`.

### 6.3. File kho

- v1.2: `{"items": [cá thể public…]}` sắp theo id, `fresh` ghi repr đầy đủ. Kho rỗng `{"items": []}`. Đọc ở v1.2 mà gặp kho đếm, id trùng, kind lạ, fresh ngoài [0, 100] thì mã 2.
- `inventory.read_inventory(path, version)` trả cá thể trong code ở v1.2, dict đếm ở v1.1 (version None thì đọc từ manifest). `write_inventory(path, data, version)`.
- `GatherSim.inventory_items()` trả mảng cá thể public sắp theo id ở v1.2. `gather_end.data.inventory` cùng schema.

### 6.4. Scenario và snapshot

- `gather.hold`, `quan.stock` là mảng cá thể `{id, kind, fresh}` (v1.2). Khung `GatherSim`/`QuanSim` chuyển sang cá thể trong code và giữ nguyên id.
- `customers[].reserved` là mảng id (C kiểm trong `scenario.py`).
- Snapshot `hold`, `stock` (quán, Shop) là mảng cá thể public; `lost` trong `monster_hit`/`faint` là mảng cá thể theo thứ tự bỏ LIFO.

### 6.5. Việc của các lát (khung đã có chỗ gọi)

| Việc | Ai | Chỗ trong code |
|---|---|---|
| Hao tươi giỏ, `spoiled{item_id, kind, location: "hold"}` | B | `GatherSim._decay_hold` (gọi ở đầu bước khi `fresh_on`) |
| Hái/bắt thêm `fresh.new_item` | B | `_try_harvest`, `_try_catch` |
| Hao tươi kho, `spoiled{…, location: "stock"}` | D | `QuanSim` (sau đồng hồ, trước giữ lại) |
| Giữ chỗ theo id, giữ lại khi ươn, `unfulfillable` | C | `QuanSim` |
| Nấu tiêu đúng id, `base_price = floor(giá × trung bình fresh / 100)`, `cook_started.items` là cá thể sắp theo kind rồi id | D | `QuanSim._interact` |
| Bàn giao cá thể trong day, id Ngày kế | C | `chonoi/day.py` |
