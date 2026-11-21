# UI check Phase 1 (T032)

- Thời điểm: 2026-11-21T10:33:38+07:00
- Không có headless browser / screenshot tool → ghi kết quả curl thay ảnh.

## Lệnh
```
python3 -m chonoi.live --mode gather --port 8771
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8771/
curl -s http://127.0.0.1:8771/state
python3 -m chonoi.live --mode quan --port 8772
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8772/
curl -s http://127.0.0.1:8772/state
node --check (script tách từ index.html)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

## Kết quả
- gather `/`: HTTP 200; `/state`: HTTP 200
- quan `/`: HTTP 200; `/state`: HTTP 200
- gather snapshot: mode=gather, tick=120, time_left=10680, hold=0/12, oxygen=1800, zero_oxy=0, catch_cd=0, at_surface=True, nodes=4, fish=6
- quan snapshot: mode=quan, tick=120, money=0, shift_earned=—(chưa trong snapshot), reputation=3.0, stock={}, customers=0, stoves=[('B1', 'idle', 0)]
- HTML phục vụ được; JS cú pháp OK; HUD Phase 9 (T028–T031) trong `chonoi/web/index.html`.
- Unittest: `Ran 32 tests in ~2.9s` — **OK** (32/32).

## Trường snapshot UI hiện "—" khi thiếu
- `shift_earned` (quan): chưa có trong Session.snapshot — HUD hiện "Ca —".
- `patience_ticks` / `eat_ticks` khách: khi chưa có → "Kiên nhẫn —" / "Ăn còn —".
- Sự kiện `gather` / `fish_caught` / `node_regrown`: hiện khi sim phát (TV1–TV4).
