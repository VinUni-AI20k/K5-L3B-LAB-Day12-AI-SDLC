# Sự kiện thêm/đổi ở Test Contract v1.1

Vỏ event giữ v1.0 (`type, tick, phase, name, data`); trong `day` thêm `"day":N`. Mẫu đề: `{"type":"event","tick":0,"phase":"gather","day":1,"name":"day_plan","data":{"dishes":{"ca_loc_nuong_trui":3,"goi_bong_sung":3},"ingredients":{"ca_loc":3,"bong_sung":6}}}`. Event kết thúc pha mang **pha cũ**.

| name | data | phát khi | lát |
|---|---|---|---|
| `fish_spawned` | `{id, kind, pos}` | sinh theo lịch | 1 (TV1) |
| `monster_hit` | `{monster_id, hp, lost, pos}` — `pos` người chơi, `lost` mảng kind theo LIFO | Cá Sấu chạm | 2 (TV2) |
| `faint` | do chạm: `{cause:"monster", lost:[giỏ còn lại], hp:0}`; do ngạt: GIẢ ĐỊNH `{lost, hp:0}` không `cause` | Máu 0 | 2 (TV2) |
| `day_start` | `{}` | đầu Ngày | 4 (TV6) |
| `day_plan` | `{dishes, ingredients}` của Ngày | sau `day_start` | 4 |
| `phase_start` | `{}` (pha mới ở vỏ `phase`) | đầu mỗi pha | 4 |
| `paused`, `resumed` | `{}` | cạnh lên `pause` | 4 |
| `bought` | `{upgrade, level, price, money}` | mua thành công | 4 |
| `buy_failed` | `{action, reason}` — reason ∈ `funds, max_level, out_of_stock, unknown` | mua thất bại / lệnh không hỗ trợ | 4 |
| `shop_end` | `{reason}` — `done` / `time` | đóng Shop | 4 |

Mở rộng (chưa làm ở P2): `attack`, `monster_stunned`, `photo`, `released`, `dish_burnt {stove_id, order_id, dish_id, order_status}`, `vendor_trade`.

Dòng `end` của `day`: thêm `days_completed`; đủ Ngày → `reason:"days_complete"`.
Snapshot `day`: thêm `day, day_plan, upgrades, active_upgrades`; gather thêm `monsters[]`, `player.invuln_ticks`; Shop có `stock`, `time_left_ticks`; `state` thêm `"paused"`.

TV1 chép bảng này sang `docs/contracts/` (mục v1.1). `hold_full` giữ `{kind}` như v1.0.
