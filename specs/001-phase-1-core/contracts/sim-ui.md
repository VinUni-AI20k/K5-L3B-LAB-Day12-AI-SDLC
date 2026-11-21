# Giao diện sim ↔ client/ui (Phase 1)

UI (`chonoi/web/index.html` qua `chonoi.live`) **chỉ đọc snapshot + event**, gửi vào `move`, `interact`, `catch`. UI không chứa luật.

## Snapshot gather (đã có trong starter — không đổi tên)
`player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface}`, `hold[]`, `hold_count`, `hold_capacity`, `nodes[{id,pos,kind,ready,regrow_ticks}]`, `fish[{id,pos,kind,heading_deg}]`, chung: `time_left_ticks, money, earned, reputation, score`.

## Snapshot quan
Đã có: `player{pos}`, `stock`, `hand`, `stoves[{id,pos,state,dish,cook_ticks_left,ready_ticks}]`, `tables[{id,pos,customer_id}]`, `customers[]`.
Đề xuất thêm (chỉ thêm), khớp tên HUD đang đọc: `customers[{id, table_id, state("waiting"|"eating"), dish_id, patience_ticks_left, eat_ticks_left, reserved}]` — **tập trường cố định**, không đổ dict thô từ scenario; `stoves[].customer_id`; `hand` = chuỗi id món hoặc `null`; `shift_earned`.
Lưu ý: `meta` của `/state` không có `menu` → UI tạm hard-code tên món; thêm `menu` vào `live.py` là sửa file khung (cần team lead).

## Lệnh từ UI
| Phím | Input |
|---|---|
| WASD / mũi tên | `move [x, d]` hoặc `[x, z]` |
| E | `interact` (cạnh lên) |
| Space | `catch` (cạnh lên) |
