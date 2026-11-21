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
