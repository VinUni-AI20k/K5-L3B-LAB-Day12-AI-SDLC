# Hợp đồng: danh sách sự kiện

> Mỗi chủ lát tự điền dòng sự kiện của mình (tên, `data`). Test QA dựa vào bảng này.
> Dòng JSONL: `{"type":"event","tick":k,"phase":...,"name":<tên>,"data":<data>}`.

## Gather

| Sự kiện | `data` | Lát | Trạng thái |
|---|---|---|---|
| `dive` | `{pos}` | Lát 1 | xong |
| `surface` | `{pos}` | Lát 1 | xong |
| `oxygen_empty` | `{pos}` | Lát 1 | xong |
| `choke` | `{hp}` | Lát 1 | xong |
| `faint` | `{pos, lost}` (`lost`: kho bị mất) | Lát 1 | xong |
| `hold_full` | `{kind, count, hold_count, hold_capacity}` | Lát 1 — phát trong `_add_to_hold` | xong |
| `node_regrown` | `{node_id}` | khung | có sẵn |
| `gather_end` | `{reason, inventory: {items}}` | khung | có sẵn |
| `gather` | `{node_id, kind, count, hold_count}` | Lát 2 | xong |
| `fish_caught` | `{fish_id, kind, count, hold_count}` | Lát 2 | xong |

## Quán

| Sự kiện | `data` | Lát | Trạng thái |
|---|---|---|---|
| `customer_left` | … | Lát 3 | |
| `no_dish` | … | Lát 3 | |
| `cook_started` | … | Lát 4 | |
| `dish_ready` | … | Lát 4 | |
| `dish_picked` | … | Lát 4 | |
| `served` | … | Lát 4 | |
| `paid` | … | Lát 4 | |
| `quan_end` | `{reason, money, earned, shift_earned, reputation}` | khung | có sẵn |
