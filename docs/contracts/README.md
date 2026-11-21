# Hợp đồng tích hợp

Chốt cho Phase 1. Đổi file này hoặc schema kho thì báo cả nhóm trước (ảnh hưởng gather, quán và UI).

## 1. Schema file kho (PRD-0 mục G)

Ghi **một lần** khi có `gather_end` (`--inventory-out`). Quán chỉ đọc (`--inventory`).

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Đúng một khóa gốc `items`.
- Khóa là id nguyên liệu: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Giá trị là số nguyên `>= 0`. Mục bằng 0 bị bỏ khi ghi. Số âm hoặc id lạ thì thoát mã 2.
- Mẫu hợp lệ: `inventory.sample.json`.
- Giỏ trong sim là mảng thứ tự nhặt (`hold`, phần tử cuối là mới nhất). File kho là bản đếm, không giữ thứ tự.

## 2. Giao diện sim ↔ UI

UI chỉ đọc snapshot (`GET /state`) và gửi lệnh (`POST /input`). Không tự tính oxy, Máu, giỏ.

Lệnh mỗi tick: `{"move": [x, y], "interact": bool, "catch": bool}`. `move` mỗi thành phần trong `[-1, 1]`. Gather: thành phần thứ hai dương là lặn xuống. `interact` và `catch` là cạnh lên (nhấn một lần, một tick).

Snapshot gather mà UI được đọc:

| Trường | Ý nghĩa |
|---|---|
| `player.pos` | `[x, d]` |
| `player.oxygen_ticks`, `player.oxygen_max_ticks` | oxy còn / tối đa |
| `player.hp`, `player.hp_max` | Máu |
| `player.at_surface` | `d <= surface_depth` |
| `player.zero_oxy_ticks` | số tick đã ngạt ở mốc hiện tại (0–59) |
| `hold`, `hold_count`, `hold_capacity` | giỏ, cuối mảng là món mới nhất |
| `nodes[]` | nút hái: `id`, `pos`, `kind`, `ready`, `regrow_ticks` |
| `fish[]` | đàn cá: `id`, `pos`, `kind` |
| `time_left_ticks`, `state`, `reason` | đồng hồ và kết thúc buổi |

## 3. Sự kiện gather

Mỗi sự kiện là `(tên, data)`. Runner gắn `tick` và `phase`.

| Tên | Khi nào | `data` | Ai phát |
|---|---|---|---|
| `dive` | từ mặt nước xuống dưới nước trong tick | `{"pos": [x, d]}` | lát 1 |
| `surface` | từ dưới nước lên mặt nước | `{"pos": [x, d]}` | lát 1 |
| `oxygen_empty` | oxy từ số dương xuống 0 | `{}` | lát 1 |
| `choke` | đủ `choke_interval_ticks` tick oxy = 0 dưới nước, trừ 1 Máu | `{"hp": <máu còn>}` | lát 1 |
| `faint` | Máu về 0; giỏ đã xóa | `{}` | lát 1 |
| `gather_end` | hết buổi | `{"reason": "docked"\|"time"\|"fainted", "inventory": {"items": {...}}}` | khung / lát 1 khi ngất |
| `hold_full` | `try_add_hold` khi giỏ đầy, món không được thêm | `{"kind": <id>}` | lát 1 (hàm giỏ); TV2 gọi |
| `node_regrown` | nút hết đếm mọc lại | `{"node_id": <id>}` | khung |
| `gather` | hái được một nút | TV2 chốt | lát 2 |
| `fish_caught` | bắt được cá | TV2 chốt | lát 2 |

Cách thêm vào giỏ, dành cho TV2: gọi `GatherSim.try_add_hold(kind, events)`. Hàm nối vào **cuối** `hold`. Trả `True` nếu thêm được. Đầy thì phát `hold_full` và trả `False`. Sức chứa là `hold_capacity` trong `game.contract.json` (12).

Ngất (`fainted`): xóa hết `hold` rồi mới `gather_end`, nên kho ghi ra là `{"items": {}}`.

Sự kiện quán (khách, bếp, tiền) do TV3/TV4 điền khi viết `quan.py`, theo PRD-0 mục E và F.
