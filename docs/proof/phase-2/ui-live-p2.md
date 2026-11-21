# Bằng chứng kiểm chứng UI chơi trực tiếp — Phase 2 (`client/ui`, `duhocsinh4to10`)

## Phạm vi triển khai (Lát 4 UI)
- [`chonoi/live.py`](../../../chonoi/live.py):
  - Hỗ trợ `--mode day` (`--days 1..5`), `POST /action` (`start`, `pause`, `resume`, `toggle_pause`, `menu`, `exit`, `skip_intro`, `open_shop`, `buy`, `shop_done`) và input v1.1 (`pause`, `shop_done`, `buy`, `attack`, `photo`).
  - Xuất `menu`, `day_plan`, `screen`, `paused`, `shop`, `active_upgrades`, `last_gather_inventory`, `last_day_summary` trong `GET /state` để client không hard-code công thức hay giá Shop.
  - Tự dùng `runner.Session("day", ...)` khi lõi `chonoi/sim/day.py` có mặt; tạm ghép vòng `GatherSim → QuanSim → Shop` ở tầng live trong lúc chờ Lát 3 & 4 lõi gộp vào `main`, hoàn toàn không ảnh hưởng `chonoi.headless`.
- [`chonoi/web/index.html`](../../../chonoi/web/index.html):
  - Đủ 6 màn hình: Menu chính (`Chơi`/`Thoát`), `DayIntro` (4s/phím + danh sách Má Tư), `EveningIntro` (kho mang về), `DayResult`, `Shop` (`oxygen`/`hp`, đếm ngược 600 tick, phím `1`/`2`/`Enter`), `Summary` sau Ngày cuối.
  - Tạm dừng `Esc`/`P`: làm mờ nền, dừng mọi bộ đếm kể cả Intro và Shop, có nút `Tiếp tục` / `Chơi lại` / `Về Menu chính`.
  - HUD sáng v1.1: Máu, Oxy (`<25%` đỏ nhấp nháy), đồng hồ (`≤30s` cảnh báo), độ sâu (`≥10m` vùng Thủy quái), giỏ LIFO + danh sách Má Tư (`Đã lấy / Cần`), hồi bắt, cảnh báo **“THỦY QUÁI!”** + viền tím, **“HẾT HƠI!”**, vẽ Cá Sấu Năm Chèo (`M1`/`M2`) & Rắn Hổ Mây (`M3`), `ca_keo`, `keo_neo`, animation bơi `ut-sen-swim.png`.
  - HUD quán v1.1: đồng hồ, tiền ca / tổng, uy tín 5 sao, điểm, hỗ trợ 2 bếp / 4 bàn / thực đơn động từ `snap.menu`, tiến độ bếp/chín/cháy (`burn_s`), kiên nhẫn từng bàn (`<25%` đỏ nhấp nháy + mốc boa), món cầm kèm `order_id`, **Kho khả dụng** (tách rõ phần giữ chỗ `reserved`).
  - Chữ không chân `--hud-font: 18px` tại `1280×720` và bộ đo `FPS` trực tiếp trên thanh trên cùng.

## Kết quả kiểm chứng thực tế
- `python -m unittest tests.test_smoke_p1 tests.test_python_starter_units tests.test_team_check tests.test_ui_live tests.test_gather tests.test_quan_service -v`: **74/74 pass**.
- `python -m unittest tests.test_live -v`: **1/1 pass** → **Tổng 75/75 tests pass**.
- `python .agents/skills/check-contract/check_contract.py`: `gather: identical bytes`, `quan: identical bytes` → **`RESULT: PASS`**.
- `python tools/check_team.py`: `OK: 6 thành viên`.
- Node v22 Canvas2D/DOM render check (Menu, DayIntro, Gather với Cá Sấu đuổi + Hết hơi, Quan 2 bếp / 4 bàn / kiên nhẫn <25% / kho khả dụng, Shop + Esc Pause + phím `1`): **`ALL PHASE 2 UI VERIFICATION CHECKS PASSED!`**.
