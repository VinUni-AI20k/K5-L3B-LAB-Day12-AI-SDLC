# Danh mục sự kiện Phase 1 (đề xuất; khóa chính thức ở `docs/contracts/` do TV1 chốt)

Dòng JSONL: `{"type":"event","tick":k+1,"phase":..,"name":..,"data":{..}}` — runner ghi theo thứ tự sim trả về.

## gather
| name | data | phát khi |
|---|---|---|
| `node_regrown` | `{node_id}` | regrow về 0 (đã có) |
| `dive` | `{pos}` | mặt nước → dưới nước trong bước |
| `surface` | `{pos}` | dưới nước → mặt nước |
| `oxygen_empty` | `{}` | oxy từ >0 xuống 0 |
| `choke` | `{hp}` | đủ `choke_interval_ticks` ở oxy 0 |
| `faint` | `{}` | hp = 0 (ngay sau `choke`) |
| `gather` | `{node_id, kind, count}` | hái thành công |
| `fish_caught` | `{fish_id, kind, count}` | bắt thành công |
| `hold_full` | `{kind}` (theo `docs/contracts/` của TV1) | không đủ chỗ cho lượt nhặt |
| `gather_end` | `{reason, inventory:{items}}` | docked / time / fainted (đã có) |

## quan
| name | data | phát khi |
|---|---|---|
| `customer_arrived` | `{customer_id, table_id, dish_id}` | lượt khách có bàn + món |
| `no_dish` | `{}` | lượt khách nhưng không món nào nấu được |
| `customer_left` | `{customer_id, table_id}` | hết kiên nhẫn |
| `cook_started` | `{stove_id, dish_id, customer_id}` | interact bếp idle |
| `dish_ready` | `{stove_id, dish_id}` | nấu xong |
| `dish_picked` | `{stove_id, dish_id}` | interact bếp ready, tay rỗng |
| `served` | `{customer_id, table_id, dish_id}` | interact bàn, tay đúng món |
| `paid` | `{customer_id, price, tip}` | ăn xong |
| `quan_end` | `{reason, money, earned, shift_earned, reputation}` | hết giờ (đã có) |

Tên sự kiện quan khớp `QUAN_HUD_EVENTS` trong `chonoi/web/index.html`. Trường `data` là `GIẢ ĐỊNH` (PRD-0 mục E chưa đọc được); dùng `dish_id` vì HUD đọc `data.dish_id`. Câu hỏi gốc: Q-D (`docs/research/phase-1.md` mục 7). TV1 chốt ở `docs/contracts/` (T002), TV5 khóa bằng test (T037).
