# Feature Specification: Phase 2 — Một ngày ở chợ nổi (day loop, Test Contract v1.1)

**Feature Branch**: không tạo branch (làm trên `tv6/phase-1-team-ai`); thư mục `specs/002-day-loop/`
**Created**: 2026-11-21 · **Status**: Draft (đã clarify theo đề; chỗ đề im lặng ghi `GIẢ ĐỊNH`)
**Input**: TICKET-02 — `docs/prd/phase-2-ticket-02.md` (bản chép đầy đủ) + `docs/research/phase-2.md` (diff contract, bản đồ ảnh hưởng, test cũ sẽ vỡ).
**Phụ thuộc**: `specs/001-phase-1-core/` (lõi P1, đã sửa theo số chuẩn). **Lõi P1 hiện CHƯA code xong**: `gather.py` mới có lát 1 (oxy, ngạt, ngất, `try_add_hold`); hái, bắt cá và toàn bộ `quan.py` vẫn `TODO(nhóm)` → là ưu tiên P0 của phase này.

> Mọi số dưới đây là **số chuẩn** của TICKET-02, phải nằm trong `game.contract.json` (v1.1) và luật chỉ đọc từ đó. 60 tick/s, tiền theo nghìn đồng.

## User Scenarios & Testing *(mandatory)*

### User Story 0 — Hoàn tất lõi P1 với số chuẩn (Priority: P0, chặn mọi story)
Hái, bắt cá, toàn bộ quán (khách, bếp, bưng, tiền, boa, uy tín, đóng ca) chạy đúng `specs/001-phase-1-core` đã cập nhật.
**Independent Test**: AC-P1-01…24 xanh với contract v1.1 (regression P1).

### User Story 1 — Số chuẩn v1.1, cá bơi và sinh thêm (P1)
Contract v1.1 có đủ 6 nguyên liệu, 6 món, nút N5/N6, cá kèo. Cá bơi 1.5 m/s trong miền của loài, đổi hướng theo seed mỗi 120 bước, phản xạ mép; sinh thêm theo lịch.
**Independent Test**: `--mode gather` không input, đọc `fish[]` và `fish_spawned`.
**Acceptance**:
1. Tick 0 có đúng 8 đàn ở 8 điểm sinh khác nhau (trong 36 cặp loài–vị trí), đúng dải sâu của loài.
2. Mỗi bước, cá di chuyển 1.5/60 m; ở bước bơi thứ 120, 240… đổi hướng theo seed **trước** khi di chuyển.
3. Tới mép x ∈ [4,96] / dải d của loài: phản xạ phần dư, đảo thành phần vuông góc; chạm góc đảo cả hai.
4. Tại `phase_tick = 360·k` (k ≥ 1), sau khi cá bơi: nếu < 12 đàn và có điểm cách mọi đàn sống > 1 m → sinh 1 đàn (`fish_spawned {id,kind,pos}`), trọng số linh 40 / lóc 30 / kèo 30 chuẩn hóa lại theo loài còn điểm; hết điểm → bỏ lượt. Cá mới bơi từ bước sau.
5. `random_fish:false` → không cá mặc định, không bơi/sinh, cá fixture đứng yên. Khai `fish` khi cờ bật → thay đàn đầu, vẫn bơi/sinh.
6. Bắt cá dùng vị trí cá **trước** khi bơi trong bước; yield linh 3, lóc 1, kèo 2.

### User Story 2 — Cá Sấu Năm Chèo, Máu, ngất, rơi hàng LIFO (P1)
Cá Sấu tuần tra, đuổi khi người chơi ở sâu và gần, chạm làm mất Máu và rơi nửa giỏ theo LIFO.
**Independent Test**: scenario `gather.monsters[]` + `player.pos`; đọc `monsters[]`, `monster_hit`, `faint`.
**Acceptance**:
1. Ngày 1 (và `gather` độc lập): M1 tuần tra [60,24]↔[64,24], 1.0 m/s; tới waypoint thì đổi mục tiêu cho bước sau. M2 [85,18]↔[89,18] có từ Ngày 3.
2. Người chơi ở d ≥ 10 và cách ≤ 10 m → `chase` 3.0 m/s; cách > 16 m hoặc người chơi lên d < 10 → về `patrol`. Cá Sấu bị chặn trong biên và d ∈ [10,30].
3. Sau khi cả hai di chuyển, khoảng cách ≤ 1.5 m, người chơi d ≥ 10 (đề :49), `invuln_ticks = 0` → `monster_hit {monster_id,hp,lost,pos}`: −1 Máu, bỏ `floor(n/2)` món theo LIFO (`lost` theo thứ tự rơi), `invuln_ticks = 90`. Tối đa một hit/bước, con gần nhất, hòa theo id.
4. Con gây hit vào `recoil` 60 bước từ bước sau, lùi 2/60 m/bước theo hướng xa người chơi chốt lúc chạm (trùng tâm → +x), chặn mép, không gây hit; hết recoil về `patrol`.
5. Trong bất tử: không hit, không recoil do chạm. Ngạt vẫn trừ Máu (xuyên bất tử), không rơi hàng.
6. Máu 0 do chạm → `faint {cause:"monster", lost:[phần giỏ còn lại], hp:0}` ngay sau `monster_hit` → `gather_end(fainted)` kho rỗng, bỏ bước còn lại; trong `day` vẫn mở quán với kho rỗng.

### User Story 3 — Quán 2 bếp / 4 bàn / 6 món + kế hoạch ngày (P1)
**Independent Test**: `--mode quan --inventory` (6 món) và `--mode day` (lọc theo kế hoạch).
**Acceptance**:
1. Bếp B1 [2,8], B2 [5,8]; bàn T1 [9,2], T2 [13,2], T3 [9,6], T4 [13,6]; khách ngồi ghế trống id nhỏ nhất.
2. Quán riêng: khách chọn đều theo seed trong 6 món đủ nguyên liệu (sau trừ giữ chỗ). Trong `day`: lọc menu theo id món trong kế hoạch Ngày **trước** khi lọc nguyên liệu; được gọi tiếp kể cả đã đủ số suất kế hoạch.
3. Bếp lấy đơn reserved cũ nhất theo `order_tick` rồi id bàn.
4. `day_plan` có đúng D1–D5 theo bảng §2; `ingredients` = Σ công thức × số suất.

### User Story 4 — Vòng ngày `--mode day`, Shop, pause (P1)
DayIntro → gather → EveningIntro → quan → DayResult → Shop → Ngày kế (hoặc tổng kết sau Ngày 5).
**Independent Test**: `--mode day --days N`; đọc `day_start`, `day_plan`, `phase_start`, `bought`, `shop_end`, dòng `end`.
**Acceptance**:
1. Đầu Ngày: `day_start` → `day_plan {dishes,ingredients}` → `phase_start(gather)`. Sau `gather_end` dựng quán với kho bàn giao (trong bộ nhớ, schema kho v1.0) và phát `phase_start(quan)` cùng tick, kể cả ngất. Sau `quan_end` dựng Shop, `phase_start(shop)` cùng tick. Pha mới chạy gameplay từ bước sau.
2. Snapshot đổi pha ghi pha mới với `phase_tick:0`; event kết thúc mang pha cũ. Mọi snapshot `day` có `day, day_plan, upgrades, active_upgrades`. Snapshot Shop có `stock` dư và `time_left_ticks` tới lúc đóng.
3. Shop: frame `"buy":"oxygen"` / `"buy":"hp"` mua cấp kế tiếp; đủ đúng giá vẫn mua; trừ `money`, giữ `earned`/điểm → `bought {upgrade,level,price,money}`. Thiếu tiền / đã tối đa / lệnh không hỗ trợ → `buy_failed {action,reason ∈ funds|max_level|out_of_stock|unknown}`, tiền và cấp giữ nguyên. Xử lý một `buy` trước cạnh `shop_done`, kể cả bước cuối.
4. Shop đóng bằng `shop_done` → `shop_end(done)`; tự đóng sau 600 tick hoạt động → `shop_end(time)`. Đóng Shop thì `days_completed += 1`, kết thúc hoặc dựng Ngày kế ngay tick đó; chỉ khi dựng Ngày mới mới chép `upgrades` → `active_upgrades`.
5. Giữ qua Ngày: `money`, `earned`, uy tín, cấp. Oxy và Máu hồi đầy theo cấp hiệu lực (oxy 45/60 s, Máu 4/5), giỏ làm mới, kho dư bỏ sau Shop.
6. Một Ngày không pause ≤ 22 200 tick (10 800 + 10 800 + 600). Dòng `end` của `day` có `days_completed` (số Shop đã đóng); đủ Ngày thì `reason:"days_complete"`.
7. `pause` (cạnh lên, cả ba mode, xét trước): vào pause chỉ tăng `tick` ngoài, phát `paused`; khi pause bỏ qua cạnh hành động, `sim_tick`, `phase_tick`, lịch, timer (cả Shop) đứng yên. Cạnh lên tiếp → `resumed`, chạy gameplay ngay bước đó. Giữ nút qua đổi pha không tạo cạnh mới.
8. `--days` chỉ với `day`, nguyên 1–5, mặc định 1; sai → mã 2. `--inventory`/`--inventory-out` không dùng với `day` (GIẢ ĐỊNH). Scenario `day` cấm `quan.stock`, `quan.reputation`; `0 ≤ money ≤ earned`; `day.day_plan` khai sai `ingredients` → mã 2.

### User Story 5 — Client UI: menu, màn chuyển, pause, Shop, HUD mới (P2 — Cursor)
Menu chính (Chơi/Thoát), DayIntro (tự chuyển 4 s hoặc phím), EveningIntro, DayResult, Summary, pause menu (Tiếp tục/Về menu), Shop UI, HUD sáng/quán theo §2. Chữ ≥ 18 px ở 1280×720, ≥ 30 FPS. Chỉ đọc snapshot/event; tắt ở headless.

### Edge Cases
- Ngạt và hit cùng tick: ngạt trước, Máu 0 → `faint` + `gather_end` ngay sau `choke`, bỏ bước còn lại.
- Cập bến cùng tick với bắt cá/hết giờ: bến thắng (nếu còn Máu).
- Hết giờ ở mọi độ sâu → `time`, giữ giỏ.
- Hit khi giỏ 1 món: `floor(1/2) = 0`, `lost = []`, vẫn −1 Máu.
- Shop đóng ở Ngày cuối vẫn cần thiết để Ngày hoàn tất.
- Đóng Shop bằng nút ở bước cuối (tick 600) → `shop_end(done)`, không phải `time`.
- Pause trong Shop: đồng hồ Shop đứng yên.
- `buy` frame lặp lại (chuỗi) chỉ chạy tại frame khai báo.
- Sinh cá khi mọi điểm đều bị chiếm (≤ 1 m) → bỏ lượt, không event.
- Đàn bị bắt bị loại (GIẢ ĐỊNH, clarify #14) → có thể tạo điểm trống cho lượt sinh sau.

## Requirements *(mandatory)*

### Contract v1.1 (lát 1)
- **FR-201**: `contract_version: "1.1"`. Thêm khóa theo §4.1: `fish_initial` = 8 (số), `fish_speed, fish_turn_ticks, fish_max, fish_spawn_ticks, fish_spawn_clearance, fish_x, fish_depths, fish_spawn_x, fish_spawn_depths, fish_weights`; `fish_yield` đủ 3 loài; nút N5/N6 (`keo_neo`); `gather.monsters` (`species.ca_sau{...}`, `spawns[]`, `invuln_ticks:90`, `loss_ratio:0.5`); `quan` thêm B2, T2–T4; `menu` 6 món; `day_plan` 5 mục; `shop {max_ticks, upgrades.oxygen[], upgrades.hp[]}`.
- **FR-202**: Nguyên liệu hợp lệ: `ca_loc, ca_linh, ca_keo, bong_dien_dien, bong_sung, keo_neo` (kho, scenario, inputs).

### Gather (lát 1–2)
- **FR-203**: Cá bơi/đổi hướng/phản xạ/sinh theo US1; RNG qua luồng riêng (`fish_turn`, `fish_spawn`, GIẢ ĐỊNH tên).
- **FR-204**: Cá Sấu theo US2 (patrol/chase/recoil, hit, LIFO, bất tử 90).
- **FR-205**: Thứ tự bước gather v1.1: đồng hồ, cooldown, bất tử, hồi nút → bơi, oxy, ngạt (Máu 0 → `faint`, `gather_end`, dừng) → (Lao nếu có) → quái theo id rồi tối đa một hit → tương tác (bến trước hái) → bắt cá (vị trí cá trước khi bơi) → hết giờ → nếu còn giờ: cá bơi, sinh theo lịch.
- **FR-206**: Snapshot gather thêm `monsters[]` (`id,kind,pos,state,target_idx,state_ticks_left,recoil_dir`), `player.invuln_ticks`; `fish[].age_ticks`.

### Quán (lát 3)
- **FR-207**: 2 bếp, 4 bàn, 6 món từ dữ liệu; luật P1 (đã sửa theo số chuẩn) áp cho mọi bếp/bàn.
- **FR-208**: Trong `day`, lọc menu theo kế hoạch Ngày trước khi lọc nguyên liệu; quán riêng dùng cả 6 món.

### Day / Shop / pause (lát 4)
- **FR-209**: `--mode day [--days N]`, máy trạng thái pha `gather → quan → shop → (day+1)` theo US4; bàn giao kho trong bộ nhớ.
- **FR-210**: Shop + nâng cấp theo dữ liệu; cấp mua hiệu lực từ Ngày kế.
- **FR-211**: Input mới: `pause` (cả 3 mode), `shop_done` (Shop), `buy` (chuỗi, chỉ tại frame khai báo). Nút đúng kiểu nhưng sai pha → bỏ qua.
- **FR-212**: Event mới và `data`: xem [contracts/events-v1.1.md](contracts/events-v1.1.md).
- **FR-213**: Scenario `day {money,earned,reputation,upgrades,day_plan}`; `gather`/`quan` là mẫu khởi tạo mỗi Ngày; kiểm mâu thuẫn trên kho thực lúc mở quán → mã 2.
- **FR-214**: Headless một Ngày (≤ 22 200 tick) chạy ≤ 20 s; tất định từng byte.

### Acceptance Criteria (headless JSONL)

| AC | Nội dung | FR | Mode / cách kiểm |
|---|---|---|---|
| AC-P2-01 | Contract v1.1 nạp được, đủ 6 nguyên liệu, 6 món, N1–N6, B1–B2, T1–T4, D1–D5, shop | FR-201/202 | `quan --ticks 0` snapshot `stoves`/`tables`; unit đọc contract |
| AC-P2-02 | Regression P1: AC-P1-01…24 xanh với số chuẩn | FR-207 | gather/quan |
| AC-P2-03 | Tick 0 có 8 đàn ở 8 điểm khác nhau, đúng dải loài | FR-203 | gather, snapshot 0 |
| AC-P2-04 | Cá bơi 1.5 m/s, đổi hướng ở bước 120·k trước khi bơi, phản xạ mép/góc | FR-203 | gather, scenario 1 đàn cạnh mép |
| AC-P2-05 | Sinh cá tại `phase_tick = 360·k`, trần 12, clearance > 1 m, bỏ lượt khi hết điểm | FR-203 | gather 4000 tick đếm `fish_spawned` |
| AC-P2-06 | `random_fish:false` → cá fixture đứng yên, không sinh | FR-203 | gather |
| AC-P2-07 | Bắt cá dùng vị trí trước khi bơi; yield kèo 2; thiếu chỗ cả đàn → `hold_full` | FR-205 | gather |
| AC-P2-08 | Cá Sấu patrol 1.0 m/s, đổi waypoint bước sau khi tới | FR-204 | gather, người chơi ở mặt nước |
| AC-P2-09 | Chase khi d ≥ 10 và ≤ 10 m (3.0 m/s); về patrol khi > 16 m hoặc d < 10 | FR-204 | gather |
| AC-P2-10 | `monster_hit`: −1 Máu, rơi `floor(n/2)` LIFO, `lost` đúng thứ tự, bất tử 90 | FR-204 | gather, giỏ 5 món → lost 2 món cuối |
| AC-P2-11 | Recoil 60 bước, lùi 2/60 m/bước, không hit; trùng tâm dùng +x | FR-204 | gather |
| AC-P2-12 | Bất tử chặn hit; ngạt xuyên bất tử, không rơi hàng | FR-204 | gather `invuln_ticks` |
| AC-P2-13 | Máu 0 do chạm → `faint{cause:"monster",lost,hp:0}` → `gather_end fainted`, kho `{}` | FR-204 | gather `hp:1` cạnh Cá Sấu |
| AC-P2-14 | Thứ tự bước v1.1 (ngạt trước hit; bến trước bắt cá/hết giờ) | FR-205 | gather fixture cùng tick |
| AC-P2-15 | M2 chỉ xuất hiện từ Ngày 3 | FR-204 | day --days 3, snapshot `monsters` |
| AC-P2-16 | Quán 4 bàn: ghế trống id nhỏ nhất; 2 bếp nấu song song | FR-207 | quan |
| AC-P2-17 | Quán riêng chọn trong 6 món; `day` chỉ món kế hoạch | FR-208 | quan vs day |
| AC-P2-18 | `day` phát `day_start{} → day_plan → phase_start{}` ở tick 0, vỏ event có `"day":1`; `day_plan` đúng bảng D1 (khớp dòng mẫu §4.4) | FR-209 | day --days 1 |
| AC-P2-19 | `gather_end` → `phase_start(quan)` cùng tick; kho bàn giao = `gather_end.inventory`; ngất → quán kho rỗng | FR-209 | day + `gather.hold` + interact tick 0 |
| AC-P2-20 | `quan_end` → `phase_start(shop)` cùng tick; snapshot Shop có `stock`, `time_left_ticks` | FR-209 | day |
| AC-P2-21 | Snapshot đổi pha: pha mới, `phase_tick:0`; event kết thúc mang pha cũ | FR-209 | day |
| AC-P2-22 | `buy:"oxygen"` đủ tiền → `bought`, money giảm, earned giữ; thiếu → `buy_failed funds`; tối đa → `max_level`; lệnh lạ → `unknown` | FR-210 | day, scenario `day.money/earned` |
| AC-P2-23 | Cấp mua hiển thị ngay ở `upgrades`, chỉ vào `active_upgrades` khi dựng Ngày kế; Ngày kế oxy max 2700 | FR-210 | day --days 2 |
| AC-P2-24 | `shop_done` → `shop_end(done)`; 600 tick → `shop_end(time)`; `days_completed` tăng | FR-209 | day |
| AC-P2-25 | Một Ngày không input ≤ 22 200 tick; dòng `end` có `days_completed` = N và `reason:"days_complete"` | FR-209 | day --days 1 --ticks 22200 |
| AC-P2-26 | Giữ money/earned/uy tín qua Ngày; Máu/oxy hồi đầy; giỏ mới | FR-209 | day --days 2 |
| AC-P2-27 | `pause`: `paused`, snapshot `state:"paused"`, `sim_tick`/`phase_tick`/timer đứng; `resumed` chạy ngay bước đó | FR-211 | gather/quan/day |
| AC-P2-28 | `--days` ngoài 1–5 hoặc dùng với mode khác → mã 2; scenario `day` có `quan.stock` → mã 2; `--mode day` không còn mã 2; nút `attack`/`photo` khi chưa bật → bỏ qua, mã 0 | FR-209/213 | CLI |
| AC-P2-29 | Tất định: `day --days 2` chạy 2 lần giống từng byte | FR-214 | day |
| AC-P2-30 | Hiệu năng: `day --days 1` ≤ 20 s | FR-214 | đo thời gian |
| AC-P2-31 | Smoke tích hợp `gather --inventory-out` → `quan --inventory`, snapshot kho tick 0 khớp; lưu `docs/proof/phase-2/integration.*` | FR-209 | gather + quan |

### Key Entities
- **DayState**: day, days_completed, money, earned, reputation, upgrades{oxygen,hp}, active_upgrades, day_plan, phase ∈ {gather, quan, shop}.
- **Monster**: id, kind (`ca_sau`), pos, waypoints[2], target_idx, state ∈ {patrol, chase, recoil}, state_ticks_left, recoil_dir.
- **FishSchool**: id, kind (linh/lóc/kèo), pos, heading_deg, age_ticks.
- **Shop**: time_left_ticks (600 hoạt động), stock dư, lệnh buy.
- **DayPlan**: day, dishes{id:n}, ingredients{id:n}.

## Success Criteria *(mandatory)*
- **SC-201**: AC-P2-01…31 có test/scenario; ≥ 90% xanh trước tag `phase-2`, phần chưa đạt ghi trung thực ở `docs/verification/phase-2.md`.
- **SC-202**: Regression P1 100% xanh với số chuẩn; test cũ đổi đều ghi lý do.
- **SC-203**: Một Ngày headless ≤ 20 s; 5 Ngày chạy hết không lỗi.
- **SC-204**: Người chơi thử chơi trọn 1 Ngày trên UI (menu → Summary/Ngày 2) không cần đọc code.

## Clarifications

### Session 2026-11-21 (theo bản đề đầy đủ; đề im lặng → GIẢ ĐỊNH)
Đã xác nhận bởi đề (bản đầy đủ): `contract_version:"1.1"`; snapshot `state:"paused"` khi pause; `faint` do chạm `{cause:"monster", lost:[giỏ còn lại], hp:0}`; `end.reason:"days_complete"`; `day_start`, `phase_start` có `data:{}` (pha nằm ở vỏ `phase`); vỏ event trong `day` thêm `"day":N`; `day_plan` phát ở tick 0; `buy` nhận `"oxygen"`, `"hp"`; `ca_keo_nuong` nấu 6 s; đàn cá bơi/sinh, hồi đầy Máu/oxy mỗi Ngày.
- Q: Hit cần người chơi ở đâu? (P2-Q7) → A: đã xác nhận bởi đề (`docs/prd/phase-2-ticket-02.md:49`): khoảng cách ≤ 1.5 m, người chơi ở `d ≥ 10`, hết bất tử.
- Q: `faint` do ngạt có `cause`? (P2-Q3) → A: GIẢ ĐỊNH (clarify #30): `{hp:0, lost}`, không `cause`.
- Q: Không làm Lao thì nút `attack` trong inputs? (P2-Q6) → A: nút đúng kiểu nhưng mở rộng chưa bật → **bỏ qua, mã 0** (đề §4.2); phải sửa `test_smoke_p1.py:65-67` và `test_python_starter_units.py:46-50`.
- Q: Đàn bị bắt có biến mất? (P2-Q9) → A: GIẢ ĐỊNH (clarify #33): có.
- Q: `--inventory`/`--inventory-out` với `day`? → A: GIẢ ĐỊNH: mã 2 ("hai cờ file kho vẫn dành cho hai mode độc lập").
- Q: Tên luồng RNG, reset theo Ngày? → A: GIẢ ĐỊNH: `fish_init`, `fish_turn`, `fish_spawn`, `quan_order`; một `Streams` cho cả lượt chạy, không reset theo Ngày.
- Q: `extensions` trong manifest là mảng hay object? (P2-Q8) → A: GIẢ ĐỊNH (clarify #32): mảng mã (`[]` khi chưa làm).
- Q: Pause có làm đứng `time_left_ticks` và đồng hồ Shop? → A: có (đề §2, §4.2).

## Assumptions
- Phase 2 **bắt buộc** sửa file khung (`headless`, `inputs`, `inventory`, `contract`, `scenario`, `runner`, `live`) — `docs/research/phase-2.md` mục 3; giao TV6 (lát 4) + TV1 (contract/inventory). Test cũ sẽ vỡ: `test_smoke_p1.py:45` (6 → 8 đàn), `:65-67` (`attack` → mã 0), `:70-77` (`--mode day` không còn mã 2), `test_python_starter_units.py:46-50` (`attack`) → TV5 sửa, ghi lý do.
- Không làm mở rộng trong lõi phase này; đề xuất `burn` và `snake` cho Phase 3 (rẻ, tái dùng luật bếp và luật quái).
- `team_size = 6` → nhóm 6 phải làm ≥ 2 mở rộng trong cả buổi lab.
