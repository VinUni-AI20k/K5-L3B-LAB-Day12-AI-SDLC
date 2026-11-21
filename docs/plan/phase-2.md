# Kế hoạch Phase 2 — Ticket-02 "Một ngày ở chợ nổi" (1:00–1:55)

Yêu cầu: [`docs/prd/phase-2.md`](../prd/phase-2.md) · Test Contract v1.1 · hạn tag `phase-2` 1:55.
Chia việc theo vai trong [`TEAM.md`](../../TEAM.md). **Định dạng dùng chung (dễ xung đột) chốt ở [`docs/contracts/README.md` mục "Hợp đồng v1.1"](../contracts/README.md#hợp-đồng-v11-phase-2--chốt-chung-cả-nhóm-đọc-trước-khi-code)** — đọc trước khi code.

## 0. Hiện trạng
| Ở đâu | Có gì |
|---|---|
| tag `phase-1` (`665f05a`) | Phase 1 đủ 4 lát + test lát 2, contract v1.0, 115 test OK (3 skip) |
| `main` (`d763e50`): đã merge `feat/lat-5-day` (Tiệp, PR #7) | `--mode day`, `--days`, `DaySim`, `ShopSim`, pause ở 3 mode; dữ liệu `day_plan`, `shop`, 3 món mới; nút `pause`/`shop_done`/chuỗi `buy`; `QuanSim(carry=...)`; clarify #4–#8; `tests/test_day_p2.py` |
| **chưa ai làm** | `contract_version: "1.1"`; số chuẩn gather (8 đàn, cá kèo, N5/N6, `fish_*`, `monsters`); B2, T2–T4; kind `ca_keo`/`keo_neo` trong `inventory.py`; cá bơi/sinh; Cá Sấu; khai `extensions`; HUD/menu Phase 2 |
| `docs/verification/phase-1.md` | còn ghi lát 4 "chưa đạt" (ghi ở `7d85efa`) → cập nhật cho tag `phase-1` |

## 0b. Tiêu chí chấp nhận Phase 2 (AC-P2-xx) — nguồn duy nhất cho test và `docs/verification/phase-2.md`
Mỗi test ghi mã AC trong docstring (ví dụ `"""AC-P2-04: ..."""`). QA nối mã AC → test → bằng chứng → kết quả.

| Mã | Tiêu chí (Ticket-02) | Người chịu trách nhiệm | Kiểm bằng |
|---|---|---|---|
| AC-P2-01 | `contract_version: "1.1"`, số chuẩn mục 1.1–1.3, đủ 6 nguyên liệu và 6 món theo dữ liệu, `extensions` khai đúng | s0ra1n0 | test contract + snapshot tick 0 |
| AC-P2-02 | Cá bơi 1.5 m/s trong miền loài, đổi hướng theo seed mỗi 120 bước, phản xạ mép/góc; `random_fish:false` đứng yên | mhoo40 | test hộp đen gather |
| AC-P2-03 | 8 đàn đầu ca; sinh cá mỗi 360 tick, trần 12, khoảng cách > 1 m, trọng số loài; `fish_spawned`; bắt cá kèo, hái kèo nèo | mhoo40 | test hộp đen gather |
| AC-P2-04 | Cá Sấu M1/M2 theo Ngày: patrol/chase/thoát chase, hit −1 Máu + bỏ floor(n/2) LIFO + bất tử 90, recoil 60 bước; `monster_hit`; ngất `cause:"monster"` vẫn mở quán với kho rỗng | s0ra1n0 | test hộp đen gather + day |
| AC-P2-05 | Quán 2 bếp, 4 bàn, 6 món: bàn trống id nhỏ nhất, chọn đối tượng (khoảng cách, bếp trước bàn, id), bếp lấy đơn cũ nhất | trongnghia2304 (khách), nguyenhung1901 (bếp) | test hộp đen quán |
| AC-P2-06 | `--mode day --days 1..5`: thứ tự `day_start → day_plan → phase_start`, kế hoạch D1–D5 đúng, khách chỉ gọi món trong kế hoạch, kho bàn giao trong bộ nhớ, tiền/earned/uy tín giữ qua Ngày, `days_completed`, `days_complete`. **Shop:** mua cấp kế tiếp, đủ đúng giá vẫn mua, `buy_failed` funds/max_level/unknown, `shop_end` done/time (600 tick), cấp mua chỉ hiệu lực từ Ngày kế (oxy 45/60 s, Máu 4/5). Một Ngày ≤ 20 s | tiepnnk01-10 (vòng ngày, Shop), trongnghia2304 (lọc món) | `tests/test_day_p2.py`, `tests/test_quan_p2.py` |
| AC-P2-07 | Pause ở cả 3 mode: `paused`/`resumed`, chỉ tăng `tick`, `sim_tick`/`phase_tick`/timer đứng yên, bỏ cạnh hành động và `buy` khi pause, snapshot `state:"paused"` | tiepnnk01-10 | `tests/test_day_p2.py` |
| AC-P2-08 | UI: menu chính, DayIntro/EveningIntro/DayResult/Summary, menu pause, HUD sáng và HUD quán theo Ticket mục 2, chữ ≥ 18 px ở 1280×720 | tiepnnk01-10, nguyenhung1901 (HUD quán) | ảnh chụp/ghi hình trong `docs/proof/phase-2/` |
| AC-P2-09 | Smoke tích hợp gather `--inventory-out` → quan `--inventory` với v1.1, stock tick 0 khớp kho | tiepnnk01-10 | `docs/proof/phase-2/integration.*` |
| AC-P2-10 | Regression P1 còn hiệu lực đạt với số chuẩn; test đổi có ghi lý do trong commit | tiepnnk01-10 | toàn bộ test + `verify.py --phase 2` |
| AC-P2-11 | Cùng seed, tham số, đầu vào → JSONL và file kho giống từng byte ở cả 3 mode | tiepnnk01-10 | `determinism.txt` |
| AC-P2-12 | Mở rộng `burn`: `ready_ticks > 1200` thì cháy, thử giữ lại cho đơn (`reserved`/`unfulfillable`), đúng 1200 vẫn bưng được; `dish_burnt` | nguyenhung1901 | test hộp đen quán + README |

Đánh số theo test đã có của Tiệp (`test_ac_p2_06_*` gồm cả Shop, `test_ac_p2_07_*` là pause), không đổi tên test.

## 1. Thứ tự merge (tránh xung đột)
1. ~~**`feat/lat-5-day`** (Tiệp)~~ — **đã merge** (PR #7, `d763e50`). Lát 0 làm tiếp trên `main` hiện tại.
2. **`feat/p2-lat0`** (s0ra1n0) — phần còn lại của nền v1.1 (mục 2). Chỉ nhánh này được sửa `game.contract.json`, `contract.py`, `inventory.py`, phần gather của `scenario.py` (xem bảng sở hữu file).
3. Các nhánh tính năng: `feat/p2-monsters`, `feat/p2-fish`, `feat/p2-quan`, `feat/p2-ui` — rebase/merge `main` sau bước 2 rồi mới mở PR.

## 2. Việc từng người (đánh dấu `[x]`, ghi commit/PR bên cạnh)

### s0ra1n0 — lát 1, Integrator
- Làm ngay:
  - [ ] Cập nhật `docs/verification/phase-1.md` cho tag `phase-1` (`665f05a`): lát 2, lát 4 → đạt, link bằng chứng; ghi tag gắn trễ
  - [ ] **Lát 0 (sau khi `feat/lat-5-day` merge), nhánh `feat/p2-lat0`, merge chậm nhất phút 20:**
    - [ ] `game.contract.json`: `contract_version: "1.1"`; gather: N5/N6 `keo_neo`, `fish_initial` 8 đàn, `fish_yield` 3 loài, `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x`, `fish_depths`, `fish_spawn_x`, `fish_spawn_depths`, `fish_weights`, `monsters`; quán: B2, T2–T4, `burn_s: 20`; `"extensions": ["burn"]` ở gốc (contracts I-1)
    - [ ] `contract.py`: bỏ ràng buộc v1.0 (đúng 6 đàn, 2 loại nút, 2 loài cá), kiểm khóa mới
    - [ ] `inventory.py`: thêm `ca_keo`, `keo_neo`
    - [ ] `scenario.py` phần gather: `monsters[]`, `fish[].age_ticks`, `player.invuln_ticks`; kind mới
    - [ ] `gather.py` `step()`: thêm sẵn lời gọi rỗng `_update_monsters`, `_move_fish`, `_spawn_fish` đúng thứ tự Ticket 4.5 (bảng ở contracts)
    - [ ] Tạo sẵn khối `# --- trạng thái lát 1/2` trong `__init__`/`snapshot()` của `gather.py` (contracts mục A)
    - [ ] Sửa `tests/test_smoke_p1.py`, `tests/helpers.py` và test cũ đổi vì số chuẩn, ghi lý do trong commit
- Sau lát 0 (nhánh `feat/p2-monsters`):
  - [ ] Cá Sấu M1 (Ngày 1), M2 (từ Ngày 3): patrol 1.0 m/s, chase 3.0 m/s (d ≥ 10, ≤ 10 m), thoát chase (> 16 m hoặc d < 10), chặn theo dải độ sâu
  - [ ] Hit ≤ 1.5 m: −1 Máu, bỏ floor(n/2) LIFO, bất tử 90, recoil 60 bước 2/60 m; `monster_hit`; `faint cause:"monster"`; tách `_faint(cause, lost, events)`
  - [ ] `GatherSim(..., day=1)` và báo Tiệp truyền `day` từ `DaySim`
- Cuối phase: [ ] `verify.py --phase 2`, đẩy tag `phase-2` trước 1:55
- Xong khi: contract v1.1 chạy, test Cá Sấu xanh, tag đã đẩy.

### mhoo40 — lát 2
- Làm ngay (viết test trước bằng scenario `fish[]`, `random_fish`):
  - [ ] Test hộp đen cá bơi/sinh theo Ticket 1.1 (bắt đầu đỏ, xanh dần)
- Sau lát 0 (nhánh `feat/p2-fish`):
  - [ ] `_move_fish`: 1.5 m/s trong x ∈ [4,96], dải độ sâu theo loài; đổi hướng theo seed ở bước bơi 120, 240… (trước khi di chuyển, theo `age_ticks`); phản xạ phần quãng còn lại, chạm góc đảo cả hai
  - [ ] `_spawn_fish`: mỗi `phase_tick = 360·k` sau khi cá bơi, trần 12, điểm cách mọi đàn > 1 m, trọng số linh 40 / lóc 30 / kèo 30 chuẩn hóa theo loài còn điểm, chọn đều điểm, hướng theo seed; `fish_spawned`; cá mới tham gia từ bước sau
  - [ ] `random_fish: false` tắt bơi + sinh; bắt cá kèo (yield 2), hái kèo nèo N5/N6
- Xong khi: test xanh, chạy 2 lần cùng seed giống từng byte.

### trongnghia2304 — lát 3, PO
- Làm ngay:
  - [x] Merge `feat/lat-5-day` (PR #7, `d763e50`)
  - [x] Đọc lại phần quán trong `day.py` sau merge: `QuanSim(carry)`, `allowed_dishes`, thứ tự sự kiện đổi pha — không lỗi
  - [ ] **PO:** duyệt giả định clarify #4–#8 của Tiệp; hỏi Anh Năm #1, #6 và các chỗ mơ hồ mới; đánh số clarify (chỉ PO cấp số mới)
  - [ ] Chốt với cả nhóm mục "Hợp đồng v1.1" trong `docs/contracts/README.md` (phút 0–5)
- Sau khi `feat/lat-5-day` merge (nhánh `feat/p2-quan`):
  - [x] Test hộp đen lọc món theo `day_plan` qua `--mode day` (khách chỉ gọi món trong kế hoạch, `no_dish` khi thiếu) — `tests/test_quan_p2.py`, bằng chứng `docs/proof/phase-2/lat3-p2-unittest.txt`
- Sau lát 0:
  - [ ] Bỏ skip 2 test cần ≥ 2 bàn, kiểm 4 bàn (bàn trống id nhỏ nhất, nhiều khách cùng lúc)
- Xong khi: test quán 4 bàn + lọc kế hoạch xanh; clarify Phase 2 có quyết định.

### nguyenhung1901 — lát 4
- Làm ngay:
  - [ ] Mở rộng **burn** đã chốt bật (contracts I-1): s0ra1n0 ghi `"extensions": ["burn"]`, `quan.burn_s: 20` ở lát 0; Hùng sửa test đang giả định `burn_s: null` để tự dựng tuning lõi (ghi lý do), gắn mã AC-P2-12
  - [ ] Mục "Mở rộng" trong README kèm bằng chứng burn
- Sau lát 0 (nhánh `feat/p2-quan`, cùng trongnghia2304 — chia hàm như Phase 1):
  - [ ] Kiểm 2 bếp B1/B2 + 4 bàn + 6 món: chọn đối tượng (khoảng cách, bếp trước bàn, id), bếp lấy đơn cũ nhất
  - [ ] Test quán trong day: tiền/uy tín giữ qua Ngày, `shift_earned` riêng từng ca
  - [ ] Hỗ trợ Tiệp HUD quán v1.1 (kiên nhẫn từng bàn đổi màu < 25%, tiến độ 2 bếp)
- Xong khi: test quán v1.1 xanh, mở rộng khai đúng và có bằng chứng.

### tiepnnk01-10 — QA lead, UI, Scrum/Release
- Làm ngay:
  - [x] Merge `feat/lat-5-day` (PR #7)
  - [ ] Khung `docs/verification/phase-2.md` (mỗi AC-P2-xx một dòng); smoke tích hợp phút 20 → `docs/proof/phase-2/integration.*`
  - [ ] UI: menu chính (Chơi/Thoát), menu pause (Tiếp tục/Về menu, làm mờ nền), DayIntro (tự chuyển 4 s), EveningIntro, DayResult, Summary
- Sau lát 0 + Cá Sấu + cá bơi:
  - [ ] Truyền `day` vào `GatherSim` trong `DaySim` (Cá Sấu theo Ngày)
  - [ ] HUD sáng: Máu, oxy < 25% nhấp nháy, thời gian ≤ 30 s đổi màu, độ sâu, giỏ theo loại, đã lấy/cần, hồi bắt, "Thủy quái!" + viền tím, "Hết hơi!"; chữ ≥ 18 px ở 1280×720
  - [ ] Regression P1 với số chuẩn; smoke `day --days 1` và `--days 5`; kiểm một Ngày ≤ 20 s
  - [ ] Standup phút 20 (`docs/standup.md`), retro phút 45–50 (`docs/retro.md`)
- Xong khi: `verification/phase-2.md` nối mọi AC với bằng chứng trên commit gắn tag.

## 3. Mốc thời gian
| Phút | Việc |
|---|---|
| 0–5 | Chốt "Hợp đồng v1.1" trong contracts; mọi người viết test trước |
| 5–10 | ~~Merge `feat/lat-5-day`~~ (đã xong); s0ra1n0 bắt đầu lát 0 |
| 10–20 | Lát 0 (`feat/p2-lat0`) merge chậm nhất phút 20 |
| 20 | Smoke tích hợp gather → quan, standup, điều người sang lát trễ |
| 20–40 | Cá Sấu, cá bơi/sinh, quán 4 bàn, UI; merge từng nhánh khi xanh |
| 40–45 | `day --days 1/5`, regression P1, `verify.py --phase 2`, verification |
| 45–50 | Retro |
| 50–55 | Dự phòng; s0ra1n0 đẩy tag `phase-2` |

## 4. Rủi ro
- **Lát 0 trễ** → test Cá Sấu/cá bơi viết trước bằng scenario; lát 0 commit từng phần (contract + inventory trước).
- **Xung đột file dùng chung** → tuân bảng sở hữu file ở contracts; tài liệu chung chỉ thêm dòng của mình (xem contracts mục "Tài liệu chung").
- **Nhánh để lâu** → càng lâu càng lệch `main`; merge ngay khi test xanh, mỗi PR nhỏ.
- **Tất định** → tên luồng `Streams` cố định theo bảng ở contracts; chạy `verify.py` trước mỗi merge.
