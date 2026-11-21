# UI check Phase 3 — HUD độ tươi (TV6)

- Thời điểm: 2026-11-21T11:18:00+07:00 (cập nhật T336)
- Không chụp ảnh headless → curl + kiểm chuỗi HTML.

## Lệnh
```
rg -n 'size:\s*(1[0-7]|[0-9])\b' chonoi/web/index.html   # kỳ vọng trống
node --check (script tách từ index.html)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather --port 8801
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8801/
curl -s "http://127.0.0.1:8801/?demo=fresh"
curl -s "http://127.0.0.1:8801/?demo=fresh&mode=quan"
```

## Kết quả
- size < 18: **không còn**
- Unittest: **32/32 OK** (kể `tests/test_live.py`); `node --check` OK
- live gather `/`: **HTTP 200**; demo fresh có HUD tươi + nhật ký

## HUD độ tươi (UI-only)
- `hold` / `stock`: nhận mảng `{id,kind,fresh}` **hoặc** kind string / map đếm (`asItemList`).
- Mỗi ô giỏ: thanh tươi (≥60 xanh, 30–60 vàng, <30 đỏ) + số 1 chữ số hoặc nhãn **ươn**.
- "Cần lấy" / "Kho khả dụng": **không đếm** hàng `fresh < 30`.
- Event `spoiled` → `Hàng ươn: <tên> (giỏ/kho)`.

## T336 — nhật ký cook/paid
- `cook_started`: món + `data.items` (tên + độ tươi từng cá thể); `base_price` nếu có.
- `paid`: **giá chốt** từ `base_price` (fallback `price`) + boa; thiếu → `—`.
- Demo quán: `/?demo=fresh&mode=quan` có mẫu `cook_started` / `paid`.

## Mở
- Sim chưa phát `items`/`base_price` thì UI hiện `—` an toàn.
