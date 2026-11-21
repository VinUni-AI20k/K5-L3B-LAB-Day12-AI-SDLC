# Ma trận kiểm chứng Phase 2 — P2-02 (lunaHieu)

Lượt chạy PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` — **80/80 test đạt, mã thoát Python 0**. Output stdout/stderr thực tế: [monster-survival-test.txt](../proof/phase-2/monster-survival-test.txt).

| Acceptance Criteria | Kiểm chứng | Kết quả / bằng chứng |
|---|---|---|
| AC-P2-M2-01 — Spawn & Ngày | `test_spawn_days_override_and_snapshot_order`, `test_scenario_validation_bad_monsters_exit_2_before_output`: M1 Ngày 1, M1+M2 Ngày 3, scenario thay thế mặc định và dữ liệu sai trả mã 2 trước output. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-02 — Patrol & Chase | `test_patrol_reaches_waypoint_then_targets_other_on_next_step`, `test_chase_detection_and_exit_thresholds`: tốc độ, đổi waypoint, ngưỡng phát hiện/thoát đuổi. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-03 — Hit, LIFO & bất tử | `test_hit_nearest_numeric_id_lifo_and_one_per_tick`, `test_hit_at_post_move_radius_edge_and_depth_gate`, `test_monster_hit_reports_player_position_after_movement`, `test_invulnerability_ends_at_t_plus_90`: một hit, HP, giỏ, vị trí sau bơi, ngưỡng và cooldown. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-04 — Recoil | `test_recoil_60_steps_coincident_direction_and_boundary`, `test_recoil_finishing_tick_cannot_hit`: bắt đầu từ bước sau, lùi 60 tick, kẹp biên và không hit ở tick vừa hết recoil. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-05 — Choke & faint | `test_choke_before_monster_hit_and_choke_ignores_invuln`, `test_monster_faint_loses_remaining_hold_and_inventory_empty`, hồi quy `test_invuln_khong_chan_ngat_theo_contract_v11`: thứ tự event, mất hàng LIFO và kho rỗng. | Đạt — [output test](../proof/phase-2/monster-survival-test.txt) |
| AC-P2-M2-06 — Snapshot & nâng cấp | `test_spawn_days_override_and_snapshot_order`, `test_active_upgrade_limits_and_day_spawn` và `tests/test_day.py`: `monsters[]` sắp ID, `player.invuln_ticks`, trần oxy/HP theo `active_upgrades`, snapshot vòng ngày. | Đạt sau ghép P2-03 — [P2-02](../proof/phase-2/monster-survival-test.txt), [suite sau merge](../proof/phase-2/monster-day-merge-test.txt). |

## Lý do cập nhật test Phase 1

Test Contract v1.1 mục 1.1 quy định: **“Ngạt xuyên bất tử và không làm rơi hàng”**. Nghĩa là `choke` không làm rơi nửa giỏ như `monster_hit`; nếu ngạt gây ngất thì `faint` làm mất toàn bộ phần giỏ còn lại. Vì vậy `tests/test_gather_sinh_ton.py` đổi test `test_invuln_chan_ngat` thành `test_invuln_khong_chan_ngat_theo_contract_v11`: với `invuln_ticks=1000`, sau 62 tick hết oxy phải có một `choke` và HP từ 3 xuống 2. Kỳ vọng cũ (HP vẫn 3, không có `choke`) trái với luật v1.1. Chỉ kỳ vọng bị thay đổi; test vẫn chạy headless thật.

`game.contract.json` đã ghi v1.1 và có cấu hình quái/Shop/vòng ngày sau merge. Kết quả 80/80 ở trên là bằng chứng P2-02 trước khi ghép; xem phần P2-03 và kết quả suite sau merge bên dưới.

## Ma trận truy vết P2-03 — vòng ngày

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả trên nhánh P2-03 |
|---|---|---|---|
| Ticket-02 §2, §4.1 và §4.5 · vòng ngày 1–5 | Smoke ca đầy đủ, kiểm thứ tự event và snapshot đổi pha | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.3 · kế hoạch và kho | Đối chiếu D1–D5, lọc thực đơn, test lại bàn giao kho qua hai tiến trình và mâu thuẫn khi mở quán | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.5 · Shop và trạng thái xuyên ngày | Chạy Giỏ → Quán → Shop với thao tác nấu, lấy món, phục vụ, trả tiền và mua oxy. Kiểm tra tiền, điểm và cấp áp dụng | [Test headless](../../tests/test_day.py) | Đạt |
| Ticket-02 §4.2 và §4.4 · pause | Pause Gather, Quán và Shop, kiểm tra đồng hồ, cạnh nút và lệnh mua | [Test headless](../../tests/test_day.py) | Đạt |
| Hồi quy Phase 1 và ghép cá bơi/sinh đàn P2-01 | Chạy toàn bộ test với preset v1.1, gồm luồng ngất → mở quán với kho rỗng và lịch sinh cá trong vòng ngày | [Kết quả chạy](../proof/phase-2/integration.md) | 129/129 test qua |

Bảng trên giữ nguyên bằng chứng 129/129 của P2-03 đã ghép với P2-01 trên `main`; kết quả sau khi ghép P2-02 được ghi riêng bên dưới.

## Kết quả sau merge P2-02 + P2-03

Merge `origin/main` (`b0e4a3e`) vào `feat/p2-monster-survival`: lệnh `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests` đạt **143/143 test, exit 0**. [Output test thật](../proof/phase-2/monster-day-merge-test.txt). `DaySim` truyền `day` và `active_upgrades` vào `GatherSim`; kiểm tra trực tiếp với cấp oxygen/hp 1 cho Ngày 1 là M1, Ngày 3 là M1+M2, trần oxy 2.700 tick và HP 4.

---

## Bằng chứng P2-04 trước lần merge main này (lịch sử)

# Kiểm chứng Phase 2 — phần P2-04

Ngày: 2026-11-21 (Asia/Bangkok). Nhánh `RESTAURANTEXPANSION`, nền `14cb40f`, working tree chưa commit. SHA-256 source thực chạy nằm trong `../proof/phase-2/P2-04-results.json`.

**Tổng thể PARTIAL:** Quán độc lập PASS; chưa tích hợp Day Loop/Shop/Gather v1.1 trên nhánh này. Không dùng báo cáo này để xác nhận DoD toàn Phase 2 hay gắn tag.

| AC P2-04 | Kết quả | Bằng chứng thực |
|---|---|---|
| AC1–AC4: B1/B2, T1–T4, 6 món, nấu song song | PASS | `tests/test_restaurant_expansion.py`, `P2-04-results.json`: 2 bếp cooking đồng thời, 4 món nấu/bưng/phục vụ/thanh toán, từng món chạy CLI riêng trong suite |
| AC5–AC7: tương tác, boa/uy tín, thanh toán/cleanup | PASS | 127 test pass; cạnh lên, tie/no fallback, ngưỡng boa, mixed settlement theo bàn, dọn từng đơn; P1 boundary tests giữ nguyên |
| AC8: Day Plan, tiền xuyên ngày, Shop | PARTIAL trên nhánh; ghép thử PASS | 139 test pass ở bản xuất `origin/lehuyanh@380e679` với overlay P2-04; 1 và 2 ngày có thực thu/mua nâng cấp, không sửa DaySim |
| AC9: JSONL/event/snapshot/determinism | PASS ở quan; PARTIAL toàn nhánh | Quán và day ghép thử giống từng byte; file kho hai tiến trình giống từng byte; day envelope chỉ có sau khi tích hợp P2-03 |

Chạy lại (Linux/macOS):

```sh
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/verify_p2_04.py --integration-ref origin/lehuyanh
```

Windows:

```powershell
$env:PATH = (Join-Path $PWD '.venv\Scripts') + ';' + $env:PATH
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python3 tools/verify_p2_04.py --integration-ref origin/lehuyanh
```

Kết quả đã chạy:

- Baseline: 105 test, 0 fail/error/skip (`P2-04-baseline-tests.txt`).
- Nhánh hiện tại: 127 test, 0 fail/error/skip (`P2-04-tests.txt`).
- Bản ghép riêng với P2-03: 139 test, 0 fail/error/skip (`P2-04-integrated-tests.txt`).
- Quán 10800 tick, 4 khách: money=earned=480, reputation=3.8, score=780, 4 paid và 1 quan_end; hai JSONL giống từng byte.
- Day mặc định ghép riêng: days_completed=1 tại tick 22200, đo khoảng 0.52 s trên máy hiện tại; chưa phải máy chấm.
- Day phục vụ+mua oxy: kết thúc tick 10802, money=480, earned=930, reputation=3.8; hai JSONL giống từng byte.
- Hai ngày có phục vụ, mua oxy rồi HP: tick 21604, days_completed=2, money=710, earned=1410, reputation=4.6. Ngày 2 áp bình oxy cấp 1 (2700 tick).
- Probe `--mode day --days 1` trên nhánh hiện tại: exit 2 (chưa có P2-03), được ghi như dependency, không tính PASS.

Nguồn, file sửa, cách ghép không ghi đè module khác và giới hạn kiểm chứng: [notes P2-04](../notes/P2-04.md). JSONL dung lượng lớn do verifier tạo và `.gitignore` bỏ qua; JSON/txt/fixture đủ để tái hiện.

---

# Kiểm chứng Phase 2 — P2-05 (giao diện)

Các số liệu trước khi ghép main là bằng chứng lịch sử của nhánh giao diện.

## Phạm vi đã triển khai

UI vòng ngày có hai chế độ preview. `--real-scenes` chạy Gather và Quán bằng mô phỏng thật của Contract 1.0 đã tích hợp trên `main` (`14cb40f`), chuyển giỏ vào kho và lấy kết quả từ sim. Các màn chuyển ca được điều phối bởi adapter localhost; Pause giữ tick của sim. Shop, thực đơn theo ngày và các cơ chế mới của v1.1 vẫn chờ backend P2-03. Fixture riêng vẫn dùng để kiểm UI của các màn chưa có dữ liệu thật.

## Chạy thử

```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -v
python docs/proof/phase-2/day_fixture.py --real-scenes --days 5 --port 8782
```

Mở [localhost:8782](http://127.0.0.1:8782/). Dùng **WASD/mũi tên** để di chuyển, **Space** để bắt cá, **E** để hái/cập bến/nấu/phục vụ, và **P/Esc** để tạm dừng. E chỉ tác động khi thực thể ở đúng tầm của sim; Quán đóng khi hết giờ. Shop hiện chưa cho mua.

Để xem fixture của Shop và hai bếp/bốn bàn, bỏ `--real-scenes` và dùng một cổng khác nếu cả hai mode chạy đồng thời. Fixture dùng **E** để chuyển ca theo kịch bản; P/Esc dùng để thử pause. Chạy với `--days 1` để đi thẳng đến tổng kết sau một ngày; thêm `--faint` để xem ca tối với kho rỗng. Mua bình oxy cấp 1 để kiểm hiệu lực ở ngày kế tiếp, hoặc thử mua Máu cấp 2 để xem lỗi. Giá và kết quả chỉ là dữ liệu kiểm giao diện. Fixture có chuyển màn khi hết đồng hồ Shop theo kịch bản; không mô phỏng luật đánh bắt, phục vụ hay nâng cấp.

## Giao diện web đề xuất cho P2-03

| Nguồn | Dữ liệu UI đang nhận |
|---|---|
| `GET /state` của Day | `mode: "day"`, `screen` nhận `menu`, `day_intro`, `gather`, `evening_intro`, `quan`, `day_result`, `shop`, hoặc `summary`, `day`, `days`, `tick_hz`, `paused`, `can_pause`, `events`. Khi chơi, `snapshot` chứa schema scene hiện có gồm `meta`, `tick`, thực thể; Gather có `monsters[]` với `id`, `pos`, `state` và `heading_deg` tùy chọn. |
| Dữ liệu từng màn | `menu[]` có `dish_id`, `servings`, `label` (nếu có); `needed` và `inventory` là map theo nguyên liệu; `cookable[]` là danh sách món. Khi ngất, `gather_reason: "fainted"`. `result` gồm `served`, `left`, `earned`, `tips`, `money`, `reputation`; Summary dùng tổng hợp có thẩm quyền của backend. |
| Shop | `shop` gồm `money`, `time_left_ticks`, `upgrades: {oxygen,hp}`, `options[]` với `id,label,level,price,enabled` (`enabled` tùy chọn) và `message` phản hồi mua. Trình duyệt gửi lại ID từ server. |
| Điều khiển | `POST /input` giữ `{move,interact,catch}`. `POST /action` nhận `{action,upgrade_id?}`, trong đó `action` là `start`, `continue`, `pause`, `resume`, `menu`, `buy`, hoặc `shop_done`; trả HTTP phù hợp và JSON `{ok}`. Sau lệnh, UI đọc lại snapshot trước khi đổi màn. |

Đây là lớp trình bày tạm để tích hợp, không phải phần mở rộng của JSONL headless. P2-03 cần chốt ánh xạ sang Ticket-02 trước khi nối `chonoi.live --mode day --days N`. Đồng thời chốt với P2-02 ánh xạ event trúng đòn (`crocodile_hit` trong fixture) và tên trường cá sấu. Việc pause/đóng Shop/chuyển ca/mua thuộc backend.

## Kết quả

| Kiểm tra | Kết quả |
|---|---|
| Hồi quy Phase 1 | 107 test Python qua, gồm 2 test adapter Day dùng mô phỏng thật. Headless thật cho Gather ngất, xuất `items: {}` và Quán nạp `stock: {}`. Chrome kiểm chuyển động bằng bàn phím ở cả hai mode `chonoi.live` thật. |
| Vòng 1 và 5 ngày | Chrome qua các màn từ Menu đến Summary trên fixture. Kiểm nhả phím khi blur, gửi lại input trung tính sau lỗi kết nối, P/Esc, giữ tick khi pause, phản hồi mua thất bại và nâng cấp có hiệu lực từ ngày sau. Fixture chuyển sang Summary khi Shop hết thời gian. |
| Cảnh và HUD | Fixture hiển thị 12 đàn cá, sáu loại nguyên liệu, M1/M2, hai bếp, bốn bàn, sáu món và kho rỗng khi ngất. Chrome kiểm bề ngang tại 390 px. |
| Hiệu năng | Đo số lần vẽ hoàn tất trên Chrome headless ở 1280×720, 15 giây mỗi cảnh. Gather và Quán đều đạt 60,1 FPS, vượt mốc 30 FPS. Số liệu trong [log](../proof/phase-2/browser-check.txt). |
| Adapter với sim v1.0 | Test kiểm cá lóc vào kho Quán, nấu–lấy món–phục vụ–thanh toán 72 nghìn, Pause và kho rỗng khi ngất. Chrome kiểm WASD, E hái thật, chốt giỏ tại bến và kho xuất hiện trong Quán. |
| Tích hợp v1.1 thật | Chưa chạy được `day --days 1/5` qua headless hoặc live. Khi backend có sẵn, chạy lại toàn bộ ca và xác nhận timer tự đóng Shop, thống kê cuối ngày, các giao dịch và pause. |

Ảnh từ fixture: [Gather](../proof/phase-2/gather-1280.png) · [Quán](../proof/phase-2/quan-1280.png) · [Shop](../proof/phase-2/shop-1280.png) · [Gather 390 px](../proof/phase-2/gather-390.png).

## Bộ ảnh món ăn và cá sấu

Fixture Day hiển thị đủ sáu ảnh món trong thực đơn, món có thể nấu, đơn hàng và bếp. Sprite Bà Út và cá sấu lấy từ Ảnh lab. UI vẽ cá sấu theo vị trí và trạng thái trong `snapshot.monsters`. Mô phỏng v1.0 vẫn cung cấp ba món theo contract.

```powershell
python docs/proof/phase-2/day_fixture.py --days 3 --port 8876
```

Mở [bản thử](http://127.0.0.1:8876/), chọn **Chơi** để xem thực đơn và **Ra bến** để gặp cá sấu. Nhấn **E** để chuyển sang màn chuẩn bị mở quán trong fixture.

- **108/108 test Python đạt**, gồm kiểm tra HTTP cho tám ảnh WebP. Copy lint trả 0 lỗi và 0 cảnh báo.
- Chrome kiểm thực đơn, Gather và Quán ở 1440, 1024, 820, 768, 390 và 320 px. Kiểm đủ sáu ảnh thực đơn, bốn ảnh đơn hàng và hai ảnh bếp, sprite Bà Út và cá sấu trên Canvas, chuyển ca và Pause. Nút **Ra bến** hiện ngay khi mở thực đơn ở cả sáu kích thước. Không ghi nhận tràn ngang, lỗi JavaScript hoặc HTTP.
- Design Taste Frontend báo `GATE: FAIL 20 (round 2 of 3)` cho các quy tắc trang giới thiệu như hero, section toàn màn hình và lưới `.wrap`. Kết quả màn chơi dựa trên phép kiểm Chrome trực tiếp ở trên.
- Ba món mới và hành vi cá sấu chạy theo dữ liệu fixture. Tích hợp gameplay v1.1 thật chờ backend P2.

## Giao diện màn chơi từ bản redesign

Gather và Quán dùng lại tranh nền, khung màn chơi và khay Bà Út của bản redesign. Hai bếp và bốn bàn ở fixture được đặt theo tranh quán. Tọa độ trong các ca chơi thật vẫn lấy từ snapshot.

Sau khi đổi giao diện, 108/108 test Python đạt. Chrome kiểm ảnh nền và Canvas đúng DPR, khay nằm cạnh cảnh trên desktop và xuống dưới ở màn hình hẹp. Đã kiểm thực đơn, cá sấu, hai bếp, bốn đơn, chuyển ca và Pause ở 1440, 1024, 820, 768, 390 và 320 px. Bản chạy mô phỏng thật qua kiểm di chuyển, hái, cập bến, chuyển kho sang Quán và Pause.
