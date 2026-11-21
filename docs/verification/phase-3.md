# Ma trận truy vết Phase 3 · Test Contract v1.2 "Mùa Nước Nổi"

> Chủ file: **TV5 (QA/Release)**. Nối từng AC-P3 (đặt trong [phân công Phase 3](../phan-cong.md)) với cách kiểm, bằng chứng và kết quả.
> Checkpoint TV5 chạy bằng **một lệnh** `python3 tools/qa_p3.py` → [qa-report.md](../proof/phase-3/qa-report.md) (ghi commit, chế độ chạy, máy, thời điểm).
> **Trạng thái manifest:** trên main (`66aa5fc`, sau PR #14–#17) `game.contract.json` vẫn để `contract_version: "1.1"` theo lộ trình chuyển tiếp của TV1. Vì vậy CP1–CP7 chạy trên **bản sao tạm bật `"1.2"`** (không sửa manifest thật); CP8a chạy trên repo. Khi TV1 bật 1.2 trên main, script tự chạy thẳng trên repo — chạy lại trước khi gắn tag `phase-3`.

## 1. Tiêu chí nghiệm thu

| AC | Chủ | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| **AC-P3-01** Schema cá thể hợp lệ, mã 2 cho kho đếm/id trùng/kind lạ/fresh NaN, vô hạn, ngoài miền; ghi nguyên tử, tick_limit giữ file | TV1 | `tests/test_inventory_v12.py` (11 test) + **CP3** (6 file sai + NaN qua CLI) + **CP2** (file giữ đủ chính xác) | [tv1-inventory-v12.md](../proof/phase-3/tv1-inventory-v12.md) · [qa-report CP2, CP3](../proof/phase-3/qa-report.md) | **Đạt** — mọi ca sai trả mã 2; file ghi `99.99166666666666` đúng `100 − 0.5/60` |
| **AC-P3-02** fresh 30 ươn ngay bước gather đầu, event đúng tick/id/location; hàng mới chưa hao trong bước nhận; LIFO payload cá thể | TV2 | `tests/test_gather_freshness_p3.py` + **CP1** qua CLI | [tv2-gather-freshness.txt](../proof/phase-3/tv2-gather-freshness.txt) · [cp1-spoil.jsonl](../proof/phase-3/cp1-spoil.jsonl) | **Đạt** — đúng dòng mẫu ticket: tick 1 `spoiled {item_id: I1, kind: ca_linh, location: hold}` |
| **AC-P3-03** Kho gồm phần giữ cùng hao; spoiled trước thử giữ lại; đủ hàng thì thay, thiếu thì unfulfillable; thứ tự order_tick/id bàn | TV3 | `tests/test_quan_fresh_p3.py` + **CP4** qua CLI | [tv3-fresh-stock.md](../proof/phase-3/tv3-fresh-stock.md) · [cp4-swap.jsonl](../proof/phase-3/cp4-swap.jsonl) · [cp4-short.jsonl](../proof/phase-3/cp4-short.jsonl) | **Đạt** — I1 (30.001) ươn ở tick 1 → đơn giữ lại `["I2"]`; không có I2 → `unfulfillable` |
| **AC-P3-04** Giá `floor(niêm yết × fresh TB / 100)` khi bắt đầu nấu, boa theo giá chốt, món chín giữ giá, `cook_started.items` đúng thứ tự | TV4 | `tests/test_tv4_freshness_p3.py` + **CP5** qua CLI | [tv4-bep-vong-ngay.md](../proof/phase-3/tv4-bep-vong-ngay.md) · [cp5-price.jsonl](../proof/phase-3/cp5-price.jsonl) | **Đạt** — cá lóc 50.25 hao đúng 60 bước quán → 50 → `base_price: 30` (ca từng sai thành 29 trên bản ghép tạm, đã sửa ở PR #17) |
| **AC-P3-05** File và day giữ id/kind/fresh qua chuyển pha, không hao hai lần, id tăng xuyên ngày, Shop/pause không hao | TV1 + TV4 + **TV5** | **CP2** (smoke file phút 20) + **CP6** (day 2 ngày, snapshot mỗi tick) + **CP7** (tất định) | [cp2-file.*](../proof/phase-3/cp2-file.inventory.json) · [cp6-day.jsonl](../proof/phase-3/cp6-day.jsonl) · [qa-report](../proof/phase-3/qa-report.md) | **Đạt** — snapshot quán tick bàn giao = `gather_end.inventory` (id/kind, fresh ±0.01); 40 snapshot pause và 600 snapshot Shop kho đứng yên; D2 cấp `I3, I4` với fresh mẫu 100/80; chạy lại giống từng byte |
| **AC-P3-06** HUD đọc được độ tươi/hàng ươn; regression còn hiệu lực; log khớp commit; verification | **TV5** | HUD chơi thử trên sim v1.2 thật · **CP8a** regression repo · **CP8b** suite khi bật 1.2 | ảnh [12](../proof/phase-3/ui/12-v12-real-gather-spoiled-events.jpg) · [13](../proof/phase-3/ui/13-v12-real-hold-freshness.jpg) · [14](../proof/phase-3/ui/14-v12-real-evening-matu.jpg) · [15](../proof/phase-3/ui/15-v12-real-quan-stock-freshness.jpg) · [test_suite.log](../proof/phase-3/test_suite.log) · [test_suite_v12.log](../proof/phase-3/test_suite_v12.log) | **HUD đạt, regression 124/124 trên manifest 1.1.** Khi bật 1.2: **18 test P1/P2 còn hỏng** (bảng mục 3) → **chưa đạt** cho tới khi chủ lát đổi fixture |

## 2. Checkpoint TV5 (`tools/qa_p3.py`)

| CP | Ca kiểm | Kết quả |
|---|---|---|
| CP1 | gather 1 bước không input, giỏ `I1 ca_linh fresh 30` | PASS — `spoiled` tick 1, đúng một lần |
| CP2 | Giỏ `I1 100`, `I2 57.5`, cập bến frame 0 → `--inventory-out` → `quan --inventory --ticks 0` | PASS — file `99.99166666666666 / 57.49166666666667` (đủ chính xác); `gather_end` và snapshot quán làm tròn 3 chữ số (`99.992`) trong dung sai ±0.01 |
| CP3 | v1.2 đọc kho đếm, id trùng, kind lạ, fresh 100.1, −0.1, thiếu fresh, NaN | PASS — cả 7 ca mã 2 |
| CP4 | Đơn giữ `I1` fresh 30.001, kho có/không có `I2` | PASS — giữ lại `I2` / `unfulfillable` |
| CP5 | Cá lóc 50.25 đã giữ, bấm E ở B1 tick 59 | PASS — `cook_started` tick 60, `items [{I1, ca_loc, 50}]`, `base_price 30` |
| CP6 | day 2 ngày, giỏ mẫu `I1 ca_loc 100`, `I2 bong_sung 80`, ca tối 120 tick, pause trong ca tối, Shop chạy hết 600 tick | PASS |
| CP7 | day seed 7 chạy hai lần | PASS — sha256 trùng |
| CP8a | Toàn suite trên repo (manifest 1.1) | PASS — 124/124 |
| CP8b | Toàn suite trên bản bật 1.2 | INFO — 106/124 đạt, 18 hỏng (mục 3) |

## 3. Test cần đổi theo luật mới trước khi bật v1.2

Các test dưới đây còn dựng/so **kho đếm** hoặc khẳng định `contract_version 1.1`. Theo TICKET-03 ("ghi lý do nếu test cũ bị thay bởi luật mới"), chủ lát đổi fixture sang mảng cá thể, so theo `kind` hoặc tách ca v1.1/v1.2 — không nới điều kiện kiểm.

| File | Số test | Chủ lát | Lý do hỏng khi bật 1.2 (trích [test_suite_v12.log](../proof/phase-3/test_suite_v12.log)) |
|---|---|---|---|
| `tests/test_gather_harvest.py` | 6 | TV2 | 4 ca fixture `hold` dạng kind → CLI mã 2 *"hold[0] phải là object {id, kind, fresh}"*; 2 ca so `hold == ["…"]` / file `{"bong_dien_dien": 1}` |
| `tests/test_gather_monsters.py` | 3 | TV1 | fixture `hold` dạng kind → mã 2 |
| `tests/test_gather_survival.py` | 1 | TV1 | fixture `hold` dạng kind → mã 2 |
| `tests/test_gather_fish_p2.py` | 1 | TV2 | fixture `hold` dạng kind → mã 2 |
| `tests/test_day_cycle.py` | 2 | TV4 | fixture `gather.hold` dạng kind trong day → mã 2 |
| `tests/test_quan_plan_p2.py` | 1 | TV3 | khẳng định `contract_version == "1.1"` |
| `tests/test_inventory_v12.py::test_headless_cli_v11_inventory_still_works` | 1 | TV1 | ca cố ý cho kho đếm v1.1 → đúng là mã 2 ở 1.2, cần tách/skip theo version |
| `tests/test_smoke_p1.py` | 2 | TV1 (khung starter) | fixture `hold` dạng kind → mã 2 |
| `tests/test_python_starter_units.py` | 1 | TV1 (khung starter) | đọc `hold` như chuỗi (`TypeError: string indices…`) |

Test của TV5 (`tests/test_live_day.py`, `tests/test_phase1_gameplay.py`) **đã** đổi: fixture theo version, so theo loại, thêm kiểm v1.2 (bàn giao cùng tick khớp id/kind/fresh, hàng Chợ `fresh 100` + id mới) — đạt cả trên 1.1 lẫn 1.2.

## 4. Giao diện và mở rộng (TV5)

| Mục | Kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| HUD độ tươi: thanh tươi từng ô, hàng ươn viền đỏ + 🤢, "Giỏ 8/12 · 3 ươn", Má Tư dặn chỉ đếm hàng chưa ươn | Chơi thử sim v1.2 thật | [13](../proof/phase-3/ui/13-v12-real-hold-freshness.jpg) | Đạt |
| Toast `spoiled` (id, nơi chứa) | Sim v1.2 phát `spoiled` I7, I5 | [12](../proof/phase-3/ui/12-v12-real-gather-spoiled-events.jpg) | Đạt |
| Kho quán: còn dùng / chưa ươn, tươi nhất, ⏳ giây tới lúc ươn, số ươn; trừ phần giữ theo id | Sim v1.2 thật | [15](../proof/phase-3/ui/15-v12-real-quan-stock-freshness.jpg) | Đạt |
| Má Tư chấm hàng, EveningIntro chỉ tính món nấu được từ hàng chưa ươn | Sim v1.2 thật (cá lóc ươn hết → 0 suất) | [14](../proof/phase-3/ui/14-v12-real-evening-matu.jpg) | Đạt |
| Giá dự kiến trên bong bóng gọi món | Ảnh snapshot giả lập v1.2 | [10](../proof/phase-3/ui/10-quan-new-scene-price-estimate.jpg) | Đạt (ảnh giả lập — sim thật ca này không có khách vì hàng ươn) |
| Chợ Chú Sáu theo v1.2: bán cá thể chưa ươn tươi nhất hòa id; hàng mua `fresh 100`, id mới, tách `gather_end` | `FreshnessV12ReadyTest`, `test_vendor_sell_and_buy_for_next_evening` chạy trên bản bật 1.2 | [test_suite_v12.log](../proof/phase-3/test_suite_v12.log) | Đạt (chỉ cửa sổ chơi; chưa khai `extensions`) |
| Hướng dẫn Ngày 1, đóng quán sớm, đồ họa mới | Chơi thử + `CloseEarlyTest` | [06](../proof/phase-3/ui/06-tutorial-day1-gather.jpg) · [11](../proof/phase-3/ui/11-quan-real-sim-cooking-tutorial.jpg) | Đạt (chỉ client/live, headless không đổi) |

## Đánh giá

- **Lõi v1.2 đúng luật qua CLI** (CP1–CP7 đều PASS trên bản bật 1.2): schema, ngưỡng 30, giữ lại khi ươn, giá theo độ tươi, bàn giao file/day, id xuyên ngày, Shop/pause không hao, tất định.
- **Chặn trước khi gắn tag `phase-3`:** manifest main còn `1.1`; khi bật `1.2` còn 18 test P1/P2 dùng kho đếm (mục 3). Cần chủ lát đổi fixture (kèm lý do trong commit), TV1 bật `1.2`, rồi chạy lại `python3 tools/qa_p3.py` trên commit đó — CP8b phải chuyển PASS.
- **Lưu ý cho chủ lát:** JSONL làm tròn độ tươi 3 chữ số, file kho giữ đủ chính xác — đúng ticket (dung sai quan sát ±0.01; file phải giữ nhánh ở ngưỡng 30), test so JSONL nên dùng dung sai.
