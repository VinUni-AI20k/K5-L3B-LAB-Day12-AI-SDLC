# Hợp đồng tích hợp (nên chốt sớm; hình thức do nhóm chọn)

Integrator giữ file này. Nguồn chuẩn là PRD-0 (`docs/prd/phase-1.md`, mục D, E, G); chỗ nào lệch thì PRD thắng.

## Hợp đồng v1.1 (Phase 2) — chốt chung, cả nhóm đọc trước khi code

Nguồn chuẩn: Ticket-02 (`docs/prd/phase-2.md`, mục 1–2, 4). Mục này gom **mọi định dạng mà hai người trở lên cùng đọc/ghi**, nên lệch là vỡ khi tích hợp. Muốn đổi: báo nhóm, Integrator duyệt, ghi lý do ở đây. Việc từng người: `docs/plan/phase-2.md`.

### A. Sở hữu file (chỉ người sở hữu sửa; người khác cần đổi thì nhắn người đó)
| File / vùng | Người sở hữu | Ghi chú |
|---|---|---|
| `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py` | s0ra1n0 (lát 0) | `day_plan`, `shop`, 3 món mới đã vào `main` qua `feat/lat-5-day` (PR #7); từ giờ chỉ lát 0 sửa |
| `chonoi/scenario.py` | gather: s0ra1n0 · quán: nguyenhung1901 · khối `day`: tiepnnk01-10 | mỗi người chỉ sửa hàm `_validate_<khối>` của mình |
| `chonoi/inputs.py`, `chonoi/runner.py`, `chonoi/headless.py` | tiepnnk01-10 | pause, `buy`, `--days`, mode `day` |
| `chonoi/sim/gather.py` khung: `step()`, `__init__`, `snapshot()` | s0ra1n0 | thứ tự gọi ở mục C. Trạng thái mới trong `__init__`/`snapshot()` nằm trong **khối có chú thích theo người** (`# --- trạng thái lát 1` / `# --- trạng thái lát 2`), s0ra1n0 tạo sẵn các khối ở lát 0; mỗi người chỉ thêm dòng trong khối của mình |
| `gather.py`: `_update_oxygen`, `_faint`, `_update_monsters` | s0ra1n0 | |
| `gather.py`: `_try_gather`, `_try_catch`, `_move_fish`, `_spawn_fish` | mhoo40 | |
| `gather.py`: `_add_to_hold` | dùng chung | đổi phải báo s0ra1n0 + mhoo40 |
| `chonoi/sim/quan.py` | khách (`_init_customers`, `_tick_patience`, `_settle_customers`, `_close_shift`, `_spawn_customers`, `_leave`): trongnghia2304 · bếp/phục vụ (`_tick_stoves_and_eating`, `_interact`, `_pay`): nguyenhung1901 | khung `step()`, `__init__`, `snapshot()` do **trongnghia2304** giữ; nguyenhung1901 cần thêm trạng thái/tham số thì nhắn hoặc thêm trong khối `# --- trạng thái lát 4` |
| `tests/test_smoke_p1.py`, `tests/helpers.py` | s0ra1n0 (lát 0) | dùng chung cho mọi test (`feat/lat-5-day` đã đổi cả hai, đã merge). Đổi vì số chuẩn v1.1 (6 → 8 đàn, mode `day` hợp lệ…) thì ghi lý do trong commit |
| `chonoi/sim/day.py`, `chonoi/sim/shop.py` | tiepnnk01-10 | |
| `chonoi/web/`, `chonoi/live.py` | tiepnnk01-10 (HUD quán: nguyenhung1901 hỗ trợ) | |
| `tests/test_<vùng>_*.py` | người làm vùng đó | **không sửa test của người khác**; test cũ đổi vì luật mới thì ghi lý do trong commit |

### B. Khóa trong `game.contract.json` (vị trí cố định)
- Gốc: `contract_version: "1.1"`, `team`, `team_size`, `build_cmd`, `run_cmd`, `headless_cmd`, `extensions: [...]` (mã mở rộng, ví dụ `"burn"`; chưa bật gì thì `[]`).
- `tuning.gather`: số chuẩn Ticket 1.1 + `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x` (miền `[4, 96]`), `fish_depths` (map loài → `[min, max]`), `fish_spawn_x` (danh sách), `fish_spawn_depths` (map loài → danh sách), `fish_weights` (map loài → số), `fish_yield` đủ 3 loài, `nodes` N1–N6, `fish_initial` 8 đàn.
- `tuning.gather.monsters`: `{species: {ca_sau: {patrol_speed, chase_speed, detect_radius, exit_radius, depths, hit_radius, recoil_ticks, recoil_dist}}, spawns: [{id, kind, pos, waypoints, from_day}], invuln_ticks: 90, loss_ratio: 0.5}`.
- `tuning.quan`: B1, B2; T1–T4; `burn_s: 20` vì nhóm bật mở rộng `burn` (quyết định I-1).
- `tuning.menu`: 6 món. `tuning.day_plan`: 5 object `{day, dishes, ingredients}`. `tuning.shop`: `{max_ticks, upgrades: {oxygen: [...], hp: [...]}}`.
- Luật **chỉ đọc số từ đây**, không hard-code (kể cả trong test: test đọc từ `game.contract.json`).

### C. Thứ tự một bước gather v1.1 (Ticket 4.5) và hàm phụ trách
1. đồng hồ, cooldown, giảm bất tử, hồi nút (khung)
2. bơi → `_update_oxygen` (oxy, ngạt) — s0ra1n0
3. `_update_monsters` (quái theo id, tối đa một hit) — s0ra1n0
4. interact: bến trước → `_try_gather` — khung / mhoo40
5. `_try_catch` (theo vị trí cá **trước** khi cá bơi) — mhoo40
6. hết giờ → `gather_end("time")`
7. nếu còn giờ: `_move_fish` → `_spawn_fish` — mhoo40

Máu về 0 ở bước 2 hoặc 3 → `_faint(cause, events)` phát `faint` rồi `gather_end("fainted")` và **dừng bước**. Cập bến ưu tiên trước bắt cá và hết giờ.

### D. Hàm dựng và thuộc tính `DaySim` dựa vào
| Lớp | Chữ ký | Ghi chú |
|---|---|---|
| `GatherSim` | `(tuning, scenario, streams, ids, day=1)` | `DaySim` truyền **bản sao tuning** đã áp `active_upgrades` (oxy, Máu), nên gather không nhận tham số cấp. `day` chọn Cá Sấu có `from_day ≤ day` |
| `QuanSim` | `(tuning, scenario, streams, ids, inventory=None, allowed_dishes=None, carry=None)` | `carry = {money, earned, reputation}`; `shift_earned` tính riêng từng ca |
| `ShopSim` | `(shop_tuning, money, upgrades, stock)` | `upgrades` là cấp đã mua; `DaySim` chép sang `active_upgrades` khi dựng Ngày mới |
| Mọi pha | `phase`, `done`, `reason`, `time_left_ticks`, `money`, `earned`, `reputation`, `snapshot()`, `step(inp)` | gather thêm `inventory_items()`; quán thêm `stock` |
| Input | `inp.move`, `inp.pressed(name)`, `inp.buy` (chuỗi hoặc `None`, chỉ ở đúng frame khai báo) | nút v1.1: `interact`, `catch`, `pause`, `shop_done` |

### E. Sự kiện v1.1 (tên và `data` đúng từng chữ, Ticket 4.4)
| Tên | `data` | Ai phát |
|---|---|---|
| `monster_hit` | `monster_id, hp, lost, pos` (vị trí người chơi; `lost` mảng kind LIFO) | s0ra1n0 |
| `faint` | `cause: "choke" \| "monster", lost, hp: 0` | s0ra1n0 |
| `fish_spawned` | `id, kind, pos` | mhoo40 |
| `day_start`, `phase_start` | `{}` | tiepnnk01-10 |
| `day_plan` | `dishes, ingredients` | tiepnnk01-10 |
| `paused`, `resumed` | `{}` | tiepnnk01-10 |
| `bought` | `upgrade, level, price, money` | tiepnnk01-10 |
| `buy_failed` | `action, reason (funds / max_level / out_of_stock / unknown)` | tiepnnk01-10 |
| `shop_end` | `reason (done / time)` | tiepnnk01-10 |
| `dish_burnt` (burn) | `stove_id, order_id, dish_id, order_status` | nguyenhung1901 |

Sự kiện v1.0 giữ nguyên (mục 3 bên dưới). Trong mode `day`, vỏ event có thêm `day`; event kết thúc mang pha cũ, `phase_start` mang pha mới, cùng tick.

### F. Snapshot v1.1 (trường thêm; UI chỉ đọc, gặp trường lạ thì bỏ qua)
- Chung: `state` có thêm `"paused"`.
- gather: `monsters[]` = `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}` (cùng dạng scenario), `player.invuln_ticks`. `fish[]` = `{id, pos, kind, heading_deg, age_ticks}` (quyết định I-2).
- mode `day`, mọi pha: `day, day_plan, upgrades, active_upgrades`; `phase` là `gather` / `quan` / `shop`; snapshot đổi pha ghi pha mới với `phase_tick: 0`. Shop: `stock` (kho dư), `time_left_ticks`.
- Dòng `end` của day: thêm `days_completed`; đủ Ngày thì `reason: "days_complete"`.

### G. Quy ước chung để không lệch tất định
- **Tên luồng ngẫu nhiên** (`self.rng.get(<tên>)`), mỗi tính năng một tên, không dùng chung:

  | Tên | Dùng cho | Ai |
  |---|---|---|
  | `customer_dish` | khách chọn món (đã có) | trongnghia2304 |
  | `fish_turn` | cá đổi hướng mỗi 120 bước | mhoo40 |
  | `fish_spawn` | chọn loài, điểm, hướng ban đầu khi sinh cá | mhoo40 |

  Cá Sấu không dùng ngẫu nhiên (quyết định I-3). Cần luồng mới → thêm dòng vào bảng này trước khi code.
  `DaySim` dùng **một** `Streams` và **một** `IdAllocator` cho cả lượt, nên luồng chạy tiếp qua các Ngày và id khách nối tiếp (C1, C2… không đặt lại mỗi Ngày) (quyết định I-4).
- **Tiền tố id** (cấp bằng `ids.new(<tiền tố>)`): khách `C`, cá sinh thêm `F` (nối sau F8), quái `M`, nút `N`, bếp `B`, bàn `T`. Không tự ghép chuỗi id.
- **Kiểu số:** tick, tiền, số lượng là **số nguyên**; uy tín là số thực; thời gian `_s` trong contract đổi sang tick bằng `int(round(s × 60))`.
- **Thứ tự mảng:** thực thể sắp bằng `ids.sort_by_id`; `hold` và `lost` theo thứ tự nhặt (LIFO cho `lost`); `items` trong `cook_started` sắp theo kind; map xuất ra sắp khóa.
- **Tọa độ** để khung (`jsonl.py`) làm tròn 3 chữ số; so bán kính bằng giá trị chưa làm tròn, tính cả đúng mép.

### H. Tài liệu chung (hay xung đột khi merge)
- `docs/ai-usage-log.md`, `docs/standup.md`: **chỉ thêm dòng của mình ở cuối bảng**, không sửa dòng người khác. Xung đột thì giữ cả hai dòng.
- `docs/clarify.md`: chỉ PO (trongnghia2304) cấp số mới; người khác thêm dòng với số `?`, PO đánh số khi merge.
- `docs/verification/phase-2.md`: QA (tiepnnk01-10) giữ; người làm lát gửi tên test + link bằng chứng.
- `AGENTS.md`: Integrator giữ; muốn thêm skill/lệnh thì nhắn.
- Nhánh: `feat/p2-<vùng>`, rebase/merge `main` trước khi mở PR; test xanh mới merge; người review là người dự phòng trong `TEAM.md`.

### I. Quyết định đã chốt (Phase 2)
Chốt theo Ticket-02; khi Anh Năm trả lời khác thì PO sửa ở đây và báo người bị ảnh hưởng. Đã chép sang `docs/clarify.md` #9–#12.

| # | Quyết định | Lý do | Ai làm theo |
|---|---|---|---|
| I-1 | **Bật mở rộng `burn`:** gốc manifest `"extensions": ["burn"]`, `tuning.quan.burn_s: 20` | Nhóm 5 người cần ≥ 1 mở rộng; burn đã có code + test (lát 4). Ticket 4.1: mở rộng burn = `quan.burn_s` hữu hạn + khai mã ở `extensions`. Lõi `burn_s: null` chỉ áp khi không khai mở rộng | s0ra1n0 ghi vào contract ở lát 0; nguyenhung1901 sửa test đang giả định `burn_s: null` để dựng tuning riêng (ghi lý do), thêm bằng chứng + mục README |
| I-2 | Snapshot cá có thêm `age_ticks` | Ticket cho scenario dựng `age_ticks` (số bước đã bơi) và lịch đổi hướng dựa vào nó; xuất ra để kiểm/khôi phục được. Trường thừa không làm vỡ UI | mhoo40 |
| I-3 | Cá Sấu **không** dùng ngẫu nhiên | Ticket 1.2 mô tả patrol/chase/recoil hoàn toàn bằng luật cố định, không nhắc seed | s0ra1n0 |
| I-4 | Một `Streams` + một `IdAllocator` cho cả lượt `day` | Ticket mục D: "id mới nối sau hậu tố lớn nhất … đã nạp hoặc phát **trong lượt**"; cùng seed → cùng output | tiepnnk01-10 (đã làm), mọi người không tự tạo `Streams`/`IdAllocator` mới |
| I-5 | Mã AC Phase 2 = bảng AC-P2-xx trong `docs/plan/phase-2.md` | Một nguồn duy nhất để nối test ↔ bằng chứng trong `docs/verification/phase-2.md` | mọi người ghi mã AC vào docstring test của mình |

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

## Mode `day`, Shop, pause (lát 5 — Ticket-02 mục 2, 4.2–4.5)

| Thành phần | File | Ghi chú |
|---|---|---|
| Vòng Ngày | `chonoi/sim/day.py` (`DaySim`) | gather → quan → shop → Ngày kế; chỉ gọi `step`, `done`, `snapshot`, `inventory_items` của từng pha |
| Shop | `chonoi/sim/shop.py` (`ShopSim`) | mỗi bước: đồng hồ → tối đa một `buy` → cạnh `shop_done` → hết giờ (`tuning.shop.max_ticks`) |
| Pause | `chonoi/runner.py` (`Session.step`) | ở tầng runner nên đúng cho cả 3 mode; `tick` ≠ `sim_tick` khi pause, `phase_tick` của day reset mỗi pha |
| Dữ liệu | `tuning.day_plan`, `tuning.shop` trong `game.contract.json` | kiểm ở `contract.py` (`validate_day_plan`, `_validate_shop`); `ingredients` phải = Σ công thức × số suất |

Giao diện các pha phải giữ (day.py dựa vào):
- `GatherSim(tuning, scenario, streams, ids)`: day truyền **bản sao tuning** đã thay `gather.oxygen_max_s` / `gather.hp_max` theo `active_upgrades`, nên lát 1 không cần tham số cấp. Lát 1 thêm Cá Sấu theo Ngày thì nhận thêm `day=1` (tùy chọn) và báo lát 5 để truyền vào.
- `QuanSim(..., inventory, allowed_dishes, carry)`: `carry = {money, earned, reputation}` xuyên Ngày; `shift_earned` tính riêng từng ca.
- Thuộc tính đọc được: `phase`, `done`, `reason`, `time_left_ticks`, `money`, `earned`, `reputation`; quán thêm `stock`.
- Sự kiện trong day có thêm `day`; sự kiện kết thúc mang pha cũ, `phase_start` mang pha mới, cùng tick. Ngày mới: `shop_end` → `day_start` → `day_plan` → `phase_start(gather)` cùng tick.
- Inputs v1.1 (`chonoi/inputs.py`): nút `pause`, `shop_done`; `buy` là chuỗi, chỉ có ở đúng frame khai báo (`InputState.buy`). `attack`/`photo` chưa bật.
- Giả định lát 5: `docs/clarify.md` #4–#8.

Khi đổi hợp đồng sau này: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú, tùy chọn).
