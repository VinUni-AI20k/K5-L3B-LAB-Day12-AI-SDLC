# Hợp đồng tích hợp (nên chốt sớm; hình thức do nhóm chọn)

Integrator giữ file này. Nguồn chuẩn là PRD-0 (`docs/prd/phase-1.md`, mục D, E, G); chỗ nào lệch thì PRD thắng.

## 1. Schema file kho (gather → quán), Test Contract v1.0

- **Dạng file:** `{"items": {"<kind>": <số nguyên ≥ 0>, ...}}`, chỉ có đúng khóa gốc `items`.
  - Kind hợp lệ ở P1: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
  - Kind vắng mặt tính là 0. Bên ghi bỏ các khóa có lượng 0, và sắp khóa theo id.
  - Kho rỗng là `{"items":{}}`.
  - Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json) `{"items":{"bong_sung":2,"ca_loc":1}}`.
- **Bên ghi** (`gather --inventory-out`, code ở `chonoi/inventory.py:write_inventory`, runner gọi):
  - Ghi **đúng một lần**, khi có `gather_end`, nội dung trùng `gather_end.data.inventory`.
  - Ngất thì ghi `{"items":{}}`.
  - Chạm `--ticks` trước khi buổi kết thúc thì không tạo, không ghi đè file.
  - Ghi file tạm cùng thư mục rồi thay thế nguyên tử.
- **Bên đọc** (`quan --inventory`, code ở `chonoi/inventory.py:read_inventory`):
  - Sai schema, kind lạ hoặc số âm/không nguyên thì thoát mã 2, trước khi ghi đầu ra.
  - Khai cả `--inventory` lẫn `scenario.quan.stock` thì mã 2.
  - Không khai gì thì kho rỗng.
  - Trần giỏ (`hold_capacity`) không áp lên kho quán.
- **Kiểm chứng:**
  - `tests/test_smoke_p1.py::Integration`;
  - `python .agents/skills/verify-phase/verify.py --phase 1` → `docs/proof/phase-1/inventory.txt`.

## 2. Giao diện `sim/*` ↔ `client/ui`

UI (`chonoi/live.py` + `chonoi/web/index.html`, hoặc HUD của nhóm) **chỉ đọc snapshot**, không gọi thẳng vào luật. Cả headless và live chạy cùng `runner.Session`.

| Hướng | Gì | Chi tiết |
|---|---|---|
| sim → UI | snapshot mỗi tick (`GET /state` ở live) | Trường chung `tick, mode, phase, state, time_left_ticks, money, earned, reputation, score`. |
| | gather | `player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold, hold_count, hold_capacity, nodes[{id, pos, kind, ready, regrow_ticks}], fish[{id, pos, kind, heading_deg}]` |
| | quán | `player{pos}, stock, hand, stoves[], tables[{id, pos, customer_id}], customers[]` (cấu trúc khách ở dưới) |
| sim → UI | event của tick vừa chạy | Danh sách ở mục 3; UI dùng để hiện thông báo (ví dụ "Hết hơi!" khi `oxygen_empty`). |
| UI → sim | input mỗi tick (`POST /input`) | `{"move": [a, b], "interact": bool, "catch": bool}`. `move` mỗi số trong [-1, 1], độ dài > 1 thì tự chuẩn hóa; nút chỉ tác động ở **cạnh lên**. Phím: WASD/mũi tên → `move`, E → `interact`, Space → `catch`. |

UI gặp trường chưa có thì bỏ qua, không được vỡ. Thêm trường mới vào snapshot thì phải ghi lại ở đây.

## 3. Danh sách sự kiện v1.0 (PRD-0 mục E)

| Tên | `data` | Ai phát (lát) | Ai nghe |
|---|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển | gather lát 1 | HUD, test |
| `oxygen_empty` | `oxygen_ticks: 0` | lát 1 | HUD ("Hết hơi!") |
| `choke` | `hp` sau khi trừ | lát 1 | HUD |
| `faint` | `cause: "choke", lost (LIFO), hp: 0` | lát 1 | HUD, test |
| `gather` / `node_regrown` | `node_id, kind, amount` / `node_id` | lát 2 / khung | HUD |
| `hold_full` | `action (gather/catch), node_id \| fish_id, required, free` | lát 2 | HUD |
| `fish_caught` | `fish_id, kind, yield` | lát 2 | HUD |
| `gather_end` | `reason (time/docked/fainted), inventory {items}` | khung + lát 1 | runner (ghi kho), quán |
| `customer_arrived` / `no_dish` | `order_id, table_id, dish_id` / `{}` | quán lát 3 | HUD |
| `customer_left` | `order_id, table_id, reason (patience/closing), reputation` | lát 3 | HUD |
| `cook_started` / `dish_ready` / `dish_picked` | `stove_id, order_id, dish_id` (+ `items, base_price` khi bắt đầu nấu) | lát 4 | HUD |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | lát 4 | HUD |
| `paid` | `order_id, table_id, base_price, tip, amount, reason (finished_eating/closing)` | lát 4 | HUD |
| `quan_end` | `reason: "time", money, earned, shift_earned, reputation` | lát 3 (`_close_shift`) | runner |

Một tick có nhiều event thì ghi theo **thứ tự xử lý** (mục F), rồi mới tới snapshot.

## 4. Thay đổi v1.1 (lát 0, Phase 2) — Ticket-02 mục 1, 2, 4

**Cấu hình** (`game.contract.json`, `contract_version: "1.1"`):
- **`gather`:**
  - `fish_initial` giờ là **số đàn** (8), không còn danh sách.
  - Thêm `fish_speed, fish_turn_ticks, fish_max, fish_spawn_ticks, fish_spawn_clearance, fish_x, fish_depths, fish_spawn_x, fish_spawn_depths, fish_weights`.
  - `fish_yield` đủ 3 loài; thêm nút N5/N6 (`keo_neo`).
- **`gather.monsters`:** `species.ca_sau`, `spawns[]` (M1 từ Ngày 1, M2 từ Ngày 3), `invuln_ticks: 90`, `loss_ratio: 0.5`.
  - `recoil_dist: 2.0` là **tổng** quãng lùi trong `recoil_ticks` (60), tức 2/60 m mỗi bước.
- **`quan`:** B1, B2; T1–T4. **`menu`:** 6 món. **`day_plan`:** 5 Ngày, `ingredients` = tổng công thức × số suất (code kiểm). **`shop`:** `max_ticks: 600`, `upgrades.oxygen[]`, `upgrades.hp[]`.
- **`extensions: []`** ở gốc manifest; chưa bật mở rộng nào.

**Kind nguyên liệu:** `chonoi/inventory.py:KINDS` thêm `ca_keo`, `keo_neo`. Schema file kho **không đổi**.

**Giao diện sim** (chốt mục 3 kế hoạch Phase 2):
- **`GatherSim(tuning, scenario, streams, ids, day=1, upgrades=None)`:**
  - `upgrades` là cấp **đang áp dụng** `{"oxygen": n, "hp": n}` → `self.oxygen_max`, `self.hp_max`. Snapshot `hp_max` lấy theo cấp.
  - Cá Sấu theo `day` (spawn có `from_day <= day`), hoặc `scenario.monsters` thay thế.
- **`GatherSim._spawn_one()`** (dùng chung, lát 0 tạo):
  - sinh một đàn theo luật "Sinh cá" (trọng số loài chuẩn hóa lại theo loài còn điểm, điểm cách mọi đàn > 1 m, stream `fish_spawn`);
  - trả đàn mới hoặc `False`;
  - đầu ca gọi 8 lần, không phát event. **Lát 2** gọi lại theo lịch `phase_tick = 360·k` và phát `fish_spawned`.
- **Cá trong sim:** `{id, kind, pos, heading_deg, age_ticks}`. Cá Sấu: `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}`; chưa di chuyển, việc của **lát 1** (`_update_monsters`).
- **`QuanSim(..., allowed_dishes=None)`:** đã có từ lát 3. `carry` (tiền/uy tín xuyên Ngày) để **lát 5** thêm.

**Inputs** (`chonoi/inputs.py`, mục 4.2):
- **Nút boolean:** `interact, catch, pause, shop_done, attack, photo`. Tên lạ vẫn trả mã 2. Nút đúng kiểu nhưng sai pha hoặc mở rộng chưa bật thì sim bỏ qua.
- **`buy`:** chuỗi khác rỗng, có trong `InputState.buy` **chỉ ở đúng frame khai báo**.

**Scenario** (`chonoi/scenario.py`, mục 4.3):
- `gather.monsters[]` (kiểm dải độ sâu loài, 2 waypoint, `recoil`/`stunned` cần timer dương, `recoil_dir` là vector đơn vị khi `recoil`).
- `gather.fish[].age_ticks`; cá fixture không vượt `fish_max`.
- `--mode day`: `load_scenario(..., "day", ...)` trả `{gather, quan, day}`.
  - Cấm `quan.stock` / `quan.reputation`.
  - Kiểm `0 ≤ money ≤ earned`, `upgrades` và `day_plan`.

**Headless:** thêm `--days` (chỉ với `day`, giá trị 1..5). Chạy `--mode day` vẫn báo "chưa cài" (mã 2) tới khi **lát 5** xong.

**Event v1.1 mới** (mục 4.4; lát nào phát):

| Event | Lát |
|---|---|
| `monster_hit`, `faint {cause: "monster"}` | 1 |
| `fish_spawned` | 2 |
| `day_start`, `phase_start`, `day_plan`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end` | 5 |

Trong day, vỏ event có thêm `day`.

**Test đổi vì luật mới** (lý do ghi ngay trong test):
- `test_smoke_p1`: số đàn 6 → `fish_initial`; `attack` không còn mã 2; `day` không còn bị chặn ở mức CLI.
- `test_python_starter_units`: test nút v1.1 thay cho test "attack là nút lạ".
- `test_quan_p1::test_ac_p1_22_…`: 4 bàn, nên khách fixture ngồi kín T2–T4 để vẫn kiểm "hết bàn thì bỏ lượt".

## Chia hàm theo lát (khung đã tạo sẵn, mỗi người chỉ sửa hàm của mình)

| Lát | File | Hàm sở hữu | Hàm dùng chung (sửa phải báo nhóm) |
|---|---|---|---|
| 1 | `chonoi/sim/gather.py` | `_update_oxygen` | `_add_to_hold` |
| 2 | `chonoi/sim/gather.py` | `_try_gather`, `_try_catch` | `_add_to_hold` |
| 3 | `chonoi/sim/quan.py` | `_init_customers`, `_tick_patience`, `_settle_customers`, `_close_shift`, `_spawn_customers`, `_leave` | `_change_reputation`, `_available`, `_reserve`, `_release` |
| 4 | `chonoi/sim/quan.py`, `chonoi/scenario.py` (`_validate_quan`) | `_tick_stoves_and_eating`, `_interact`, `_pay` | như lát 3 |

Thứ tự gọi trong `step()` do Integrator giữ; đổi phải đối chiếu PRD (gather mục F / Ticket-02 4.5, quán mục F).
Quán (PRD-0 mục F): đồng hồ + kiên nhẫn + nấu/ăn → di chuyển + tối đa một interact → theo id bàn: ăn xong trả tiền, hết kiên nhẫn rời (khi ca còn giờ) → hết ca thì `_close_shift` (khách ăn trả `closing`, khách chờ rời `closing`, `quan_end`) → còn giờ thì lượt khách mới.

## Cấu trúc khách (lát 3 tạo, lát 4 đọc/đổi) — theo PRD-0 mục D/F

| Trường | Kiểu | Ai ghi | Ghi chú |
|---|---|---|---|
| `id` | chuỗi | lát 3 | khách mới cấp `ids.new("C")`, nối sau id fixture; cũng là `order_id` |
| `table_id` | chuỗi | lát 3 | bàn trống id nhỏ nhất |
| `dish_id` | id món trong `menu` | lát 3 | chọn đều theo seed (stream `customer_dish`) trong món đủ nguyên liệu khả dụng |
| `order_tick` | số nguyên | lát 3 | `phase_tick` lúc đến |
| `state` | `waiting` / `eating` | lát 3 → lát 4 | lát 4 đổi sang `eating` khi `served` |
| `patience_ticks_left` | số nguyên | lát 3 | đầy = `patience_s × 60`, chỉ giảm khi `waiting`, bắt đầu từ bước sau khi đến |
| `eat_ticks_left` | số nguyên | lát 4 | 0 tới khi được phục vụ |
| `order_status` | `reserved` / `assigned` / `unfulfillable` / `served` | lát 3 → lát 4 | khách mới `reserved` |
| `reserved` | `{kind: số}` | lát 3 | = công thức món; stock chỉ trừ khi `cook_started` (lát 4 xóa `reserved`, đổi `assigned`) |
| `base_price`, `tip` | số nguyên hoặc `null` | lát 4 | `null` tới lúc chốt (xem `docs/clarify.md` #1) |

Món trên bếp / trên tay: payload `{order_id, dish_id, base_price}` (`docs/clarify.md` #2). Khách rời (`_leave`) bỏ món có `order_id` trùng.

Khi đổi hợp đồng sau này: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú, tùy chọn).
