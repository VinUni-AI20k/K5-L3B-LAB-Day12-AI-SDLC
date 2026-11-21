# Data model — Phase 1

Đơn vị thời gian: tick (`tick_hz` = 60). Mọi hằng số đọc từ `game.contract.json` → `tuning`.

## gather (`GatherSim`)

| Thực thể | Trường | Ràng buộc / chuyển trạng thái |
|---|---|---|
| Player | `pos [x,d]`, `vel`, `heading_deg` | khung lo; `d ∈ [0,30]` |
| | `oxygen_ticks` | [0, `oxygen_max_s·60`]; −1 dưới nước, +`oxygen_refill_per_tick` mặt nước |
| | `hp` | [0, `hp_max`]; −1 mỗi `choke`; 0 → faint |
| | `zero_oxy_ticks` | [0, `choke_interval_ticks`−1]; +1 mỗi tick oxy==0 dưới nước (tính cả bước chạm 0); reset khi oxy > 0, ở mặt nước, hoặc sau choke (đã xác nhận bởi TICKET-02) |
| | `catch_cd_ticks` | đặt `round(catch_cooldown_s·60)` khi bắt thành công |
| Hold | `list[kind]` | cuối = mới nhất (LIFO); `len ≤ hold_capacity` |
| Node | `id, kind, pos(d=0), regrow_ticks` | `ready ⇔ regrow_ticks==0`; hái → `regrow_s·60` |
| Fish | `id, kind, pos(d>surface), heading_deg` | đứng yên ở P1; bị loại khi bắt (GIẢ ĐỊNH clarify #14) |

Trạng thái buổi: `playing → done(reason ∈ {docked, time, fainted})`.

## quan (`QuanSim`)

| Thực thể | Trường | Ràng buộc / chuyển trạng thái |
|---|---|---|
| Stock | `{kind:n}` | n ≥ 0; trừ khi `cook_started` |
| Customer | `id, table_id, state, dish_id, order_tick, patience_ticks_left, reserved{kind:n}, eat_ticks_left, price, tip` (tập trường cố định; kiên nhẫn đầy = `patience_s·60` đọc từ tuning) | `waiting →(served) eating →(eat_ticks=0) paid/xóa`; `waiting →(patience=0) left/xóa` |
| Stove | `id, pos, state, dish, customer_id, cook_ticks_left, ready_ticks` | `idle →(interact) cooking →(cook=0) ready →(interact) idle` |
| Table | `id, pos` (+`customer_id` suy ra) | ≤ 1 khách |
| Hand | `null` hoặc id món | ≤ `carry_limit` (=1) |
| Reputation | float | kẹp [`reputation_min`, `reputation_max`]; làm tròn `round(x, 6)` sau mỗi thay đổi để `floor` trong `score` không lệch |
| Money | `money`, `earned`, `shift_earned` | += `price + tip` khi `paid` |

Giữ chỗ: `available(kind) = stock[kind] − Σ reserved[kind]` của khách chưa nấu. Món "nấu được" khi `available ≥ recipe` cho mọi nguyên liệu.

Lịch khách: tick `T_k = 120 + 900·k` = `first_customer_tick + k·round(customer_interval_s·60)`, k ≥ 0, chỉ khi có bàn trống (đã xác nhận bởi TICKET-02). Bếp lấy đơn reserved cũ nhất theo `(order_tick, table_id)`. Boa = `floor(price·tip_rate)`.

## Kho (Contract G, cố định)

`{"items":{"bong_dien_dien":n,"bong_sung":n,"ca_linh":n,"ca_loc":n}}` — bỏ mục 0, sắp id; ví dụ `docs/contracts/inventory.sample.json`.
