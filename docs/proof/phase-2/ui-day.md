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

## Ghép PixiJS (phương án A — giữ cả hai)

- Thời điểm: 2026-11-21T12:58:00+07:00
- Nền: `pixi-của-user` (canvas 2D animated sprites + particle/LERP/shake + `pixi.min.js` local; **không** CDN)
- Port từ `cursor-ui-day`: day-mode sync (`simPhase`/`userStarted`), Esc/P pause cạnh, Shop `buy`/`shop_done`/`shopFlash`, DayIntro map `dishes`/`ingredients`, HUD độ tươi/ươn, `cook_started`/`spoiled`/`paid` event lines, `?demo=…`
- Giữ render Pixi/user: `drawAnimatedFish` / monster / Út Sen / stove / table, particles, high-contrast, `?demo=warn|warnq`
- Kiểm: `node --check` OK; `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → **135 ran, OK (1 skipped)**; `tests.test_live` OK
- Live curl 200: `--mode gather` :8811, `--mode quan` :8812, `CHONOI_CONTRACT=tests/fixtures/contract-v1.1-day.json --mode day` :8813 — GET `/` + `/state`
- Grep: không `cdnjs` / URL ngoài; `text()` clamp `HUD_MIN=18` — không còn `size` < 18