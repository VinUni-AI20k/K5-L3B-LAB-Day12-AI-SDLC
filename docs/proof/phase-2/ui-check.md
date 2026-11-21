# UI check Phase 2 (client/ui TV6)

- Thời điểm: 2026-11-21T10:59:00+07:00 (cập nhật sau fix chữ ≥ 18 px)
- Không có headless browser → curl + grep size.

## Lệnh
```
rg -n 'size:\s*(1[0-7]|[0-9])\b' chonoi/web/index.html   # kỳ vọng: không khớp
node --check (script tách từ index.html)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather --port 8791
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8791/
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8791/?demo=shop"
python3 -m chonoi.live --mode quan --port 8792
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8792/
```

## Kết quả
- `size < 18`: **không còn** (text/textLoose sàn `HUD_MIN=18`, bỏ `allowSmall`).
- Layout: HUD gather `top=118`, quan `top=130`; nhãn bản đồ rút (Bến, giây mọc, `!` quái, shortDish); bảng T1–T4 rộng theo viewport.
- Unittest: **32/32 OK**; JS `node --check` OK.
- live gather `/` + `/?demo=shop` + quan `/`: **HTTP 200**.

## Demo URL
- `/?demo=menu|dayIntro|eveningIntro|dayResult|shop|summary|pause`

## Đề xuất
- Live nhận `pause` + snapshot `paused` / `day_plan` / `monsters[]` / `shift_earned`.
