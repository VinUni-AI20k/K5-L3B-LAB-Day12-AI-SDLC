# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | @minhthu27 | `quan_service.py` + `quan.py` theo schema khách mới (`dish_id`, `order_status`, `*_ticks_left`) và thứ tự bước PRD-0 F; 8 test lát 4; đã rebase main (có hợp đồng sự kiện) | Ghép `quan_customers` thật của @viethoang126, chạy lại toàn bộ test, mở PR | Chờ @viethoang126 gộp `tick_customers_timers` / `customers_leave` / `spawn_customers`; cần chốt ai giảm `eat_ticks_left` (đã làm ở lát 4) |
