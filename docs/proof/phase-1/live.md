# Kiểm chứng P1-15: cửa sổ `chonoi.live` ở cả hai chế độ

Kiểm trên Windows, Python 3.13, ngày 2026-11-21, `main` sau PR #13 (lát 3 và 4 của quán đã có).
D tiếp quản P1-15 từ C; hook `pre-push` của C được giữ nguyên tác giả ở commit riêng.

## Cách kiểm

Chạy `python -m chonoi.live --mode gather|quan --port N` thật (tiến trình riêng), gọi API bằng `urllib`:

| Bước | Kết quả quan sát |
|---|---|
| `GET /` ở cả hai chế độ | 200, trả `index.html` (15338 byte) |
| `GET /state`, gather | có `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `catch_cd_ticks`, `at_surface`), `hold`, `hold_count`, `hold_capacity`, `nodes`, `fish`, cùng `meta`, `events`, `finished`, `error`; không còn `invuln_ticks` (v1.0) |
| `POST /input {"move":[0,1]}` rồi chờ 1,2 s, gather | `pos` xuống `[2.0, 4.63]`, `at_surface` false, `oxygen_ticks` 1738, `events` có `dive` |
| `POST /restart`, gather | 200 |
| `POST /input {"move":[5,0]}` (ngoài [-1, 1]) | HTTP 400 |
| `GET /state`, quan với `--inventory` | `stock` = `{"bong_sung":2,"ca_loc":1}`, `stoves` = B1 `idle`, `tables` = T1 trống (`customer_id` null), `hand` null, `customers` rỗng |
| `POST /input {"move":[1,0]}` rồi chờ 0,8 s, quan | `pos` đi sang `[11.1, 5.0]` (tick 88) |

`web/index.html` đọc đúng tên trường theo PRD-0 (`dish_id`, `patience_ticks_left`, `hand.dish_id`, `at_surface`); trường chưa có thì bỏ qua nên không lỗi.

## Chưa kiểm

- Chưa mở `index.html` trong trình duyệt để xem hình vẽ (khung chỉ là hình khối tạm); HUD, đồ họa và âm thanh thật thuộc Phase 2.
- Khách đến, nấu, bưng, phục vụ và trả tiền được kiểm bằng test sim (`tests/test_quan_slice3.py`, `tests/test_quan_slice4.py`), chưa chơi tay trên cửa sổ live.
