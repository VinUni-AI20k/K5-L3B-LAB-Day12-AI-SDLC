# UI day-loop check (T260–T266)

- Thời điểm: 2026-11-21T11:25:00+07:00
- Contract: `CHONOI_CONTRACT=tests/fixtures/contract-v1.1-day.json` (manifest gốc còn v1.0)
- Lệnh: `CHONOI_CONTRACT=tests/fixtures/contract-v1.1-day.json python3 -m chonoi.live --mode day --port 8820`
- Unittest: **60/60 OK**; `node --check` OK; chữ ≥ 18 px

## Kết quả curl/API
- GET / 200
- start phase=gather day=1 paused=False day_plan={'dishes': {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3}, 'ingredients': {'ca_loc': 3, 'bong_sung': 6}}
- meta has shop=True upgrades={} active={}
- after pause edge paused=True tick=142
- after unpause paused=False tick=159
- after interact phase=quan
- buy while quan: last buy events []
- html markers missing: none

## UI nối snapshot
- `phase` gather|quan|shop → màn play/EveningIntro/Shop
- `day_plan.dishes`/`ingredients` (map) → DayIntro + HUD cần lấy
- `paused` ↔ Esc/P cạnh `pause`; Shop: `buy` oxygen|hp, `shop_done`
- `upgrades` / `active_upgrades` / `shop` catalog + đồng hồ 600 tick + `buy_failed`

## FPS
- Client hiện FPS trên canvas (EMA); headless không đo GPU — khi mở trình duyệt kỳ vọng ≥ 30 @1280×720 (không vẽ thừa).

## Tasks
- T260–T265: đã có menu/intros/pause/shop/HUD; T266: bằng chứng file này.