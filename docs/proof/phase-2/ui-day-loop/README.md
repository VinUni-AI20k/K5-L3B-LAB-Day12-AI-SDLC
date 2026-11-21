# Bằng chứng UI Day loop (Ticket 05/06 Phase 2) — Vinh

Client `chonoi/web/index.html` dựng lại từ bản hợp lệ của main (bản commit 1a89a37 bị hỏng cú pháp:
`const cv = docume    nt...`, mất mọi lời gọi `/input`). Kiểm:

- `node --check` trên khối `<script>`: **SYNTAX OK**.
- `python tools/run_checks.py`: PASS (191 test, smoke, tất định byte, bằng chứng).
- Chạy thật bằng Chrome headless (`drive-ui.py`, `python -m chonoi.live --mode day --days 2` + scenario rút ngắn):

| Bước | Quan sát |
|---|---|
| Menu (`1-menu.png`) | Có **Chơi** / **Thoát**; sim đứng yên (`state: paused`) |
| Chơi → intro Ngày (`2-intro.png`) | Ngày 1 + món/số suất + nguyên liệu cần lấy; sim `paused` tới khi bấm phím hoặc sau 4 s, rồi `resumed` |
| Gather (`3-gather.png`) | Bảng "Cần lấy (đã lấy/cần)" Cá lóc 2/3, Bông súng 1/6; huy hiệu Ngày |
| Esc (`4-pause.png`) | Nền mờ, Tiếp tục / Về menu; `sim_tick` và `time_left_ticks` đứng yên; Esc lần 2 → `playing` |
| Intro tối (`5-evening-intro.png`) | Món bán + nhập kho |
| Shop (`7-shop.png`, `8-shop-bought.png`) | Kết quả ngày, tiền, giá/cấp nâng cấp, đồng hồ tự đóng 10 s. Phím `1`,`1` → `bought` oxygen cấp 1, 2; phím `3` thiếu tiền → `buy_failed funds`; `upgrades.oxygen=2` nhưng `active_upgrades={}` tới khi sang Ngày mới |
| Pause trong Shop | `time_left_ticks` đứng yên |
| Enter → `shop_done` | Sang Ngày 2: `active_upgrades.oxygen=2`, tiền giữ 100 |
| Hết Ngày cuối (`C-summary.png`) | Tổng kết: tiền, điểm, uy tín, khách, món bán chạy |
| `--mode gather` / `--mode quan` | Không menu/intro, pause vẫn hoạt động |

Không lỗi JS (`pageerror`/console) trong cả hai lượt chạy. Không đổi gì trong `chonoi/*.py`.
Chưa kiểm: FPS ≥ 30 trung bình (cần `tools/bench.py` + Playwright); chữ ≥ 18 px đã nâng cho prompt/HUD chính,
nhãn nút Tương phản/Âm thanh (11–12 px) và event log còn nhỏ.
