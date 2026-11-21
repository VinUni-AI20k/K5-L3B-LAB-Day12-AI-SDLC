# Bằng chứng P2: vẽ lại hai cảnh của client web

Nhánh `p2/ui-visual` (cắt từ `main` @ `cfaa8bf`). Chỉ đổi phần hiển thị trong `chonoi/web/`.

## Ảnh chụp (1280×720, chụp từ canvas)

| File | Nguồn | Thấy gì |
|---|---|---|
| [`ui-gather-live.png`](ui-gather-live.png) | `python -X utf8 -m chonoi.live --mode gather`, bơi xuống 7 m | Trời hồng, nhà sàn, dừa nước, bến + ghe, điên điển, bông súng, cá linh đi đàn, cá lóc, Út Sen (áo bà ba, khăn rằn, kính lặn, giỏ lưới), HUD oxy/giờ |
| [`ui-gather-mock-ca-sau.png`](ui-gather-mock-ca-sau.png) | `/?mock=day-gather` | Cá Sấu đuổi ở vùng sâu: viền tím, quầng tím, chữ "Thủy quái!" trên con quái và trên HUD; oxy < 25% (đỏ) và giờ ≤ 30 s (đỏ); cá kèo, kèo nèo |
| [`ui-quan-live.png`](ui-quan-live.png) | `python -X utf8 -m chonoi.live --mode quan --inventory <kho mẫu>`, nấu xong rồi bưng | Contract hiện tại trên `main` có 1 bếp, 1 bàn: B1, T1, khách chờ có thanh kiên nhẫn, Út Sen bưng lẩu còn bốc hơi, HUD kho/tay |
| [`ui-quan-mock-v11.png`](ui-quan-mock-v11.png) | `/?mock=quan` (bố cục Test Contract v1.1) | Nhà bè, đèn dây vàng, đèn lồng, khói bếp; B1 đang nấu (vòng tiến độ + "2 s"), B2 "Chín!"; T1–T4 với ghế nhựa đỏ; khách T1 kiên nhẫn < 25% (thanh đỏ), T3 "Đang ăn" |

## Kiểm tra

- **FPS** (đếm `requestAnimationFrame` trong 3–5 s, khung 1280×720, pane hiện): gather mock 60.2, gather live 60.1, quan mock 60.1, quan live 60.1. Yêu cầu ≥ 30.
- **HUD theo TICKET-02** giữ nguyên (`js/gather/hud.js`, `js/quan/hud.js`): chữ ≥ 18 px, oxy < 25% đổi màu + nhấp nháy, giờ ≤ 30 s đổi màu, kiên nhẫn < 25% đổi màu (thanh trong bong bóng order, đỏ nhấp nháy). Chỉ đổi màu nền bản đồ nhỏ sang màu phù sa.
- **Headless/JSONL không đổi**: `git diff --stat main -- chonoi/sim chonoi/headless.py chonoi/live.py chonoi/runner.py game.contract.json docs/contracts tests` rỗng. Chạy `python -m chonoi.headless --mode gather|quan --seed 1 --ticks 600` ở nhánh này và ở bản `main` → `cmp` giống từng byte (gather sha256 `72c30e63f0ca4f4d…`, quan `359bbf1092af7f86…`).
- **RNG giao diện tách khỏi mô phỏng**: mọi chi tiết trang trí lấy từ `CN.art.hash` (hàm băm cố định), không dùng `Math.random` hay `Streams`.
- **Unittest**: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → `Ran 44 tests … OK` (gồm `test_live.py`, `test_live_static.py`).
  Lưu ý Windows: `test_smoke_p1` gọi `python3` theo `headless_cmd` trong contract; trên máy chỉ có `python` (còn `python3` là lối tắt Microsoft Store) thì 21 test đó báo lỗi `9009` dù mã đúng. Khi đặt một `python3.exe` (venv) lên PATH thì cả 44 test xanh.
