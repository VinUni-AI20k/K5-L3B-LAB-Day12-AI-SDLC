# UI check Phase 2 (client/ui TV6)

- Thời điểm: 2026-11-21T10:57:22+07:00
- Không có headless browser để chụp ảnh → curl + kiểm chuỗi HTML.

## Lệnh
```
python3 -m chonoi.live --mode gather --port 8781
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8781/
curl -s "http://127.0.0.1:8781/?demo=shop"
curl -s http://127.0.0.1:8781/state
python3 -m chonoi.live --mode quan --port 8782
curl -s http://127.0.0.1:8782/state
node --check (script tách từ index.html)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

## Kết quả
- gather `/`: HTTP 200 ; `/?demo=shop`: HTTP 200 ; `/state`: HTTP 200
- quan `/state`: HTTP 200
- gather tick=117 mode=gather oxygen=1800
- quan tick=121 mode=quan money=0 shift_earned=—(chưa có)
- Unittest: **32/32 OK**; JS `node --check` OK.
- HTML (~37KB) có menu / DayIntro / EveningIntro / DayResult / Shop / Summary, pause Esc/P, HUD Thủy quái / Hết hơi, 6 món + ca_keo/keo_neo, `?demo=…`.

## Demo URL (màn day chưa có trong live mode gather|quan)
- `/?demo=menu` · `dayIntro` · `eveningIntro` · `dayResult` · `shop` · `summary` · `pause`

## Đề xuất (không sửa khung trong task này)
- `POST /input` nhận `pause: true` và snapshot có `paused` / phase day (`day_intro`, `shop`, …), `day_plan`, `monsters[]`, `shift_earned`.
- Hiện UI gửi `pause` nhưng `live.py` bỏ qua field lạ; overlay pause hiện đề xuất khi chưa có `snap.paused`.
