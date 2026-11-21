# UI check Phase 3 — HUD độ tươi (TV6)

- Thời điểm: 2026-11-21T11:10:00+07:00
- Không chụp ảnh headless → curl + kiểm chuỗi HTML.

## Lệnh
```
rg -n 'size:\s*(1[0-7]|[0-9])\b' chonoi/web/index.html   # kỳ vọng trống
node --check (script tách từ index.html)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather --port 8801
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8801/
curl -s "http://127.0.0.1:8801/?demo=fresh"
# quán demo: ?demo=fresh&mode=quan
```

## Kết quả
- size < 18: **không còn**
- Unittest: **32/32 OK**; `node --check` OK
- live gather `/`: **HTTP 200**; `/?demo=fresh` phục vụ HTML có `fresh_snap`, `Hàng ươn`, `drawFreshSlot`, `SPOILED_BELOW`

## HUD độ tươi (UI-only)
- `hold` / `stock`: nhận mảng `{id,kind,fresh}` **hoặc** kind string / map đếm (tự nhận dạng qua `asItemList`).
- Mỗi ô giỏ: thanh tươi (≥60 xanh, 30–60 vàng, <30 đỏ) + số 1 chữ số hoặc nhãn **ươn**.
- "Cần lấy" / "Kho khả dụng": **không đếm** hàng `fresh < 30`.
- Event `spoiled` → `Hàng ươn: <tên> (giỏ/kho)`.
- Demo: `/?demo=fresh` (gather) · `/?demo=fresh&mode=quan`

## Mở / đề xuất
- Sim TV1–TV4 chưa chắc đã lộ `hold[]` cá thể / event `spoiled` — UI sẵn; khi snapshot cũ thì không có thanh tươi (coi khả dụng).
