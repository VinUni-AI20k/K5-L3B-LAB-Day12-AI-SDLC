# Hợp đồng: danh sách sự kiện

> Mỗi chủ lát tự điền dòng sự kiện của mình (tên, `data`). Test QA dựa vào bảng này.
> Dòng JSONL: `{"type":"event","tick":k,"phase":...,"name":<tên>,"data":<data>}`.

## Gather

| Sự kiện | `data` | Lát | Trạng thái |
|---|---|---|---|
| `dive` | `{pos}` (chưa đối chiếu PRD-0) | Lát 1 | xong |
| `surface` | `{pos}` (chưa đối chiếu PRD-0) | Lát 1 | xong |
| `oxygen_empty` | `{oxygen_ticks: 0}` | Lát 1 | xong |
| `choke` | `{hp}` | Lát 1 | xong |
| `faint` | `{cause, hp: 0, lost}` — cause: choke/monster; `lost`: mảng kind theo LIFO | Lát 1 | xong |
| `hold_full` | `{action, fish_id \| node_id, required, free}` | Lát 1 — phát trong `_add_to_hold`, lát 2 truyền `source` | xong |
| `node_regrown` | `{node_id}` | khung | có sẵn |
| `gather_end` | `{reason, inventory: {items}}` | khung | có sẵn |
| `gather` | … | Lát 2 | |
| `fish_caught` | … | Lát 2 | |
| `fish_spawned` | `{id, kind, pos}` (v1.1, chỉ khi sinh theo lịch) | Cá bơi/sinh | xong (sinh) |
| `monster_hit` | `{monster_id, hp, lost, pos}` — `lost`: mảng kind LIFO, `pos`: vị trí người chơi (v1.1) | Cá Sấu | |

## Quán

| Sự kiện | `data` | Lát | Trạng thái |
|---|---|---|---|
| `customer_left` | … | Lát 3 | |
| `no_dish` | … | Lát 3 | |
| `cook_started` | `{stove_id, dish, customer_id}` | Lát 4 | xong |
| `dish_ready` | `{stove_id, dish}` | Lát 4 | xong |
| `dish_picked` | `{stove_id, dish}` | Lát 4 | xong |
| `served` | `{customer_id, table_id, dish}` | Lát 4 | xong |
| `paid` | `{customer_id, table_id, dish, price, tip, total}` | Lát 4 | xong |
| `quan_end` | `{reason, money, earned, shift_earned, reputation}` | khung | có sẵn |

## Day / Shop / pause (v1.1)

| Sự kiện | `data` | Lát | Trạng thái |
|---|---|---|---|
| `day_start`, `phase_start` | `{}` | Day | |
| `day_plan` | `{dishes, ingredients}` | Day | |
| `paused`, `resumed` | `{}` | Day | |
| `bought` | `{upgrade, level, price, money}` | Shop | |
| `buy_failed` | `{action, reason}` — reason: funds/max_level/out_of_stock/unknown | Shop | |
| `shop_end` | `{reason}` — done/time | Shop | |

Trong chế độ `day`, vỏ event có thêm trường `day`.
