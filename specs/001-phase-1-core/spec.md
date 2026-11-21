# Feature Specification: Phase 1 lõi — Lặn & Hái (gather) + Mở Quán (quan)

**Feature Branch**: không tạo branch (làm trên `tv6/phase-1-team-ai`); thư mục spec `specs/001-phase-1-core/`

**Created**: 2026-11-21

**Status**: Cập nhật 2026-11-21 theo số chuẩn TICKET-02 (`docs/prd/phase-2-ticket-02.md` §1): boa floor, bếp chọn đơn theo `order_tick` rồi id bàn, ngạt reset khi oxy > 0 hoặc lên mặt nước, lịch khách 120 + 900·k, đóng ca. Các mục này **đã xác nhận bởi TICKET-02**; phần còn `GIẢ ĐỊNH` ghi rõ.

**Input**: "Phase 1 (PRD-0): buổi sáng gather (oxy, ngạt, Máu, ngất, hái nút mặt nước, bắt cá dưới nước, giỏ 12 LIFO, cập bến/hết giờ ghi kho) và buổi tối quan (khách theo lịch, kiên nhẫn, nấu, bưng, tiền, boa, uy tín); nối gather → kho.json → quan; headless tất định"

**Nguồn yêu cầu**: PRD-0 trên lab board KHÔNG đọc được bằng AI → spec dựng từ `game.contract.json`, các `TODO(nhóm)` trong `chonoi/sim/`, `chonoi/scenario.py`, `tests/test_smoke_p1.py`, `chonoi/web/index.html` (tên sự kiện HUD), `docs/plan/phase-1.md`, `docs/clarify.md`. Chỗ không chắc đánh dấu `GIẢ ĐỊNH` (xem mục Clarifications và `docs/clarify.md`).

> Quy ước: mọi số trong spec là **giá trị hiện tại của `game.contract.json`**, chỉ để minh họa; luật phải đọc từ contract. 1 s = `tick_hz` = 60 tick.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Lặn sinh tồn: oxy, ngạt, Máu, ngất (Priority: P1)

Út Sen lặn xuống sông: dưới nước oxy giảm, lên mặt nước oxy hồi. Hết oxy mà vẫn ở dưới nước thì bị ngạt, mất Máu theo chu kỳ; hết Máu thì ngất và mất cả giỏ.

**Why this priority**: Rủi ro/áp lực cốt lõi của buổi sáng; mọi việc hái/bắt dựa trên nó. Test ẩn chấm trực tiếp.

**Independent Test**: Chạy headless `--mode gather` với scenario đặt vị trí/oxy/Máu, không cần hái/bắt; đọc snapshot `player.*` và sự kiện.

**Acceptance Scenarios**:

1. **Given** người chơi ở `d = 10` (dưới nước), oxy đầy, **When** đứng yên 60 tick, **Then** `oxygen_ticks` giảm đúng 60.
2. **Given** ở mặt nước (`d ≤ surface_depth`) với oxy 100, **When** 1 tick, **Then** oxy = min(100 + `oxygen_refill_per_tick`, max).
3. **Given** bơi từ mặt nước xuống qua `surface_depth`, **When** tick vượt ranh giới, **Then** có đúng một sự kiện `dive`; bơi lên ngược lại có `surface`.
4. **Given** dưới nước, oxy = 1, **When** 1 tick, **Then** sự kiện `oxygen_empty` (một lần), oxy = 0.
5. **Given** dưới nước, oxy 0, Máu 3, **When** 60 tick, **Then** `choke`, Máu = 2, `zero_oxy_ticks` về 0.
6. **Given** dưới nước, oxy 0, Máu 1, `zero_oxy_ticks` 59, **When** 1 tick, **Then** `choke`, `faint`, `gather_end` reason `fainted` với `inventory.items = {}`; dòng `end` reason `fainted`; file kho (nếu `--inventory-out`) là `{"items":{}}`.

---

### User Story 2 — Hái nút, bắt cá, giỏ 12 LIFO (Priority: P1)

Ở mặt nước bấm `interact` gần nút hái để hái rau/bông; dưới nước bấm `catch` gần đàn cá để bắt. Mọi món vào giỏ theo thứ tự nhặt (món mới nhất ở cuối = trên cùng), tối đa 12.

**Why this priority**: Tạo nguyên liệu cho quán; không có thì quan vô nghĩa.

**Independent Test**: Scenario đặt người chơi cạnh nút/cá, inputs bấm `interact`/`catch`; kiểm `hold`, sự kiện `gather`, `fish_caught`, `hold_full`, `node_regrown`.

**Acceptance Scenarios**:

1. **Given** ở mặt nước, cách nút `ready` ≤ `interact_radius`, **When** cạnh lên `interact` (ngoài vùng bến), **Then** sự kiện `gather`, giỏ thêm `node_yield` món `kind` của nút ở cuối mảng, nút `ready=false`, `regrow_ticks = regrow_s·60`.
2. **Given** nút đang mọc lại, **When** đếm về 0, **Then** sự kiện `node_regrown`, nút `ready=true`.
3. **Given** dưới nước, `catch_cd_ticks = 0`, đàn cá trong `catch_radius`, **When** cạnh lên `catch`, **Then** `fish_caught`, giỏ thêm `fish_yield[kind]` món, đàn bị loại khỏi `fish` (GIẢ ĐỊNH, clarify #14), `catch_cd_ticks = round(catch_cooldown_s·60)` (30 tick, tính từ lần bắt thành công (đã xác nhận bởi TICKET-02)).
4. **Given** giỏ không đủ chỗ cho cả lượt nhặt, **When** hái/bắt, **Then** `hold_full`, giỏ không đổi, nút/cá/hồi chiêu không đổi.
5. **Given** ở mặt nước, **When** bấm `catch`, **Then** không có gì xảy ra. **Given** dưới nước, **When** bấm `interact` gần nút, **Then** không hái.

---

### User Story 3 — Kết thúc buổi sáng và ghi kho (Priority: P1)

Cập bến (`interact` trong vùng bến) hoặc hết giờ thì buổi sáng kết thúc, giỏ ghi ra file kho đúng một lần.

**Why this priority**: Là điểm nối gather → quan; smoke test đã kiểm.

**Independent Test**: `--inventory-out kho.json`; kiểm `gather_end`, dòng `end`, nội dung file.

**Acceptance Scenarios**:

1. **Given** trong bến, có nút trong tầm, **When** `interact`, **Then** `gather_end` reason `docked` (bến xét TRƯỚC hái, không hái).
2. **Given** `time_left_ticks = 3`, **When** chạy, **Then** `gather_end` reason `time` ở tick 3, giỏ giữ nguyên trong kho.
3. **Given** `--ticks` hết trước khi buổi kết thúc, **Then** dòng `end` reason `tick_limit`, KHÔNG ghi file kho.

---

### User Story 4 — Quán tối: khách theo lịch, kiên nhẫn, uy tín (Priority: P1)

Từ kho, quán mở; khách đến theo lịch, ngồi bàn trống, gọi một món nấu được từ kho (giữ chỗ nguyên liệu). Khách chờ quá kiên nhẫn thì bỏ đi, trừ uy tín.

**Why this priority**: Nửa còn lại của vòng lặp ngày.

**Independent Test**: `--mode quan` với `--inventory` hoặc `scenario.stock`, không cần input; quan sát `customer_arrived`, `no_dish`, `customer_left`, `reputation`.

**Acceptance Scenarios**:

1. **Given** kho nấu được ≥ 1 món và bàn trống, **When** tick = `first_customer_tick`, **Then** `customer_arrived` (customer_id, table_id, dish_id), nguyên liệu món được giữ chỗ (`reserved`).
2. **Given** khách đầu đã đến, **Then** lượt khách kế tiếp ở tick `120 + 900·k` (k ≥ 0) = `first_customer_tick + k·customer_interval_s·60`, chỉ khi có bàn trống (đã xác nhận bởi TICKET-02).
3. **Given** kho (trừ phần đã giữ chỗ) không nấu được món nào, **When** tới lượt khách, **Then** `no_dish`, không có khách ngồi.
4. **Given** khách chờ, **When** kiên nhẫn (`patience_s·60` tick) về 0 trước khi được phục vụ, **Then** `customer_left`, uy tín += `left_reputation_delta` (kẹp [0, 5]), bàn trống, giữ chỗ chưa nấu được nhả.

---

### User Story 5 — Quán tối: nấu, bưng, phục vụ, tiền, boa (Priority: P1)

Út Sen đi tới bếp bấm `interact` để nấu món khách gọi, chờ chín, lấy món (tay cầm tối đa 1), mang tới bàn bấm `interact` để phục vụ; khách ăn xong trả tiền, có thể boa và tăng uy tín.

**Why this priority**: Nguồn tiền/điểm; test ẩn chấm.

**Independent Test**: Scenario dựng sẵn khách/bếp/tay (`customers`, `stoves`, `hand`) + inputs `interact`; kiểm chuỗi `cook_started → dish_ready → dish_picked → served → paid`.

**Acceptance Scenarios**:

1. **Given** bếp `idle` trong tầm, có khách đang chờ món chưa nấu, tay rỗng, **When** `interact`, **Then** `cook_started`, nguyên liệu trừ khỏi kho, bếp `cooking`, `cook_ticks_left = cook_s·60`.
2. **When** nấu đủ, **Then** `dish_ready`, bếp `ready`.
3. **Given** bếp `ready`, tay rỗng, **When** `interact`, **Then** `dish_picked`, `hand = dish`, bếp `idle`.
4. **Given** tay cầm đúng món khách ở bàn trong tầm đang chờ, **When** `interact`, **Then** `served`, tay rỗng, khách `eating` `eat_s·60` tick.
5. **When** ăn xong, **Then** `paid` với `price` và `tip`; `money`, `earned`, `shift_earned` tăng `price + tip`; bàn trống.
6. **Given** lúc `served` (giao) kiên nhẫn còn ≥ `tip_min_patience_ratio` (≥ 30 s), **Then** `tip = floor(price·tip_rate)` và nếu tip > 0 thì uy tín += `tip_reputation` (kẹp ≤ 5); ngược lại `tip = 0`, uy tín không đổi (đã xác nhận bởi TICKET-02).
7. **Given** nhiều đối tượng trong tầm, **When** `interact`, **Then** xử lý tối đa MỘT đối tượng, chọn theo (khoảng cách, bếp trước bàn, id).
8. **When** hết giờ, **Then** `quan_end` reason `time` với money/earned/shift_earned/reputation; dòng `end` reason `time`.

---

### User Story 6 — Nối ngày + headless tất định (Priority: P1)

Chạy gather ghi `kho.json`, rồi chạy quan đọc chính file đó; mọi lượt chạy cùng seed/input cho JSONL giống từng byte.

**Independent Test**: Hai lần chạy cùng tham số → `cmp` hai file JSONL; smoke `test_inv_01_*`.

**Acceptance Scenarios**:

1. **Given** gather kết thúc với giỏ `[ca_loc, bong_sung, bong_sung]`, **When** quan `--inventory kho.json --ticks 0`, **Then** snapshot đầu `stock = {"bong_sung":2,"ca_loc":1}`.
2. **Given** cùng `--seed`, `--inputs`, `--scenario`, **When** chạy hai lần (gather hoặc quan), **Then** JSONL và file kho giống từng byte.

---

### User Story 7 — HUD tạm trên trình duyệt (Priority: P3)

Cửa sổ `python3 -m chonoi.live` hiển thị đúng các trường snapshot mới (oxy, Máu, giỏ LIFO, nút, cá; khách, bếp, tay, tiền, uy tín) và nhật ký sự kiện. Không làm đồ họa/sáng tạo ở Phase 1.

**Independent Test**: Mở live, so HUD với snapshot JSONL cùng seed.

---

### Edge Cases

- Đi qua ranh giới mặt nước nhiều lần liên tiếp: mỗi lần đổi vùng đúng một `dive`/`surface`.
- Oxy > 0 hoặc lên mặt nước khi đang ngạt: `zero_oxy_ticks` reset 0, không mất Máu (đã xác nhận bởi TICKET-02). Ngạt xuyên bất tử, không rơi hàng.
- Hai nút/đàn cá cùng khoảng cách: chọn id nhỏ hơn (`sort_by_id`).
- Giỏ còn 1 chỗ mà bắt `ca_linh` (yield 3): `hold_full`, không bắt (đã xác nhận bởi TICKET-02).
- Bến và nút cùng trong tầm: bến thắng.
- Cùng tick vừa `gather_end("docked")` vừa hết giờ: chỉ một `gather_end` (docked), sự kiện sau không xử lý.
- Quán: khách đến khi mọi bàn có người → không có khách ("nếu có bàn trống" (đã xác nhận bởi TICKET-02)); không phát sự kiện (GIẢ ĐỊNH).
- Đóng ca (hết giờ): khách đang ăn trả tiền ngay (`paid`), khách đang chờ rời mà **không** trừ uy tín, dọn món và phần giữ của đơn (đã xác nhận bởi TICKET-02).
- Tay đang cầm món mà `interact` ở bếp: không lấy/nấu; mang sai món tới bàn: không phục vụ.
- Kho rỗng: mọi lượt khách là `no_dish`.
- Scenario mâu thuẫn mức luật (khách giữ chỗ quá kho, khách `eating` thiếu giá/tip, hai khách một bàn...) → mã thoát 2, không ghi đầu ra.
- `burn_s = null` → món chín không cháy (Phase 1).

## Requirements *(mandatory)*

### Functional Requirements — gather

- **FR-001**: Oxy tính theo `d` **cuối** bước: dưới nước (`d > surface_depth`) −1/tick; mặt nước +`oxygen_refill_per_tick`; kẹp [0, `oxygen_max_s·60`].
- **FR-002**: So vùng đầu/cuối bước → `dive` / `surface` (data: `pos`).
- **FR-003**: `oxygen_empty` khi oxy từ > 0 xuống 0.
- **FR-004**: Sau khi cập nhật oxy, nếu oxy 0 và dưới nước → `zero_oxy_ticks += 1` (tính cả bước vừa chạm 0); đủ `choke_interval_ticks` → Máu −1, `choke`, đếm lại 0. Khi oxy > 0 hoặc ở mặt nước `zero_oxy_ticks = 0`; ngạt xuyên bất tử, không rơi hàng (đã xác nhận bởi TICKET-02) (căn cứ `scenario.py`: `zero_oxy_ticks ∈ [0,59]`, >0 chỉ khi oxy 0 dưới nước).
- **FR-005**: Máu 0 → `faint`, giỏ xóa, `gather_end` reason `fainted`, inventory `{}`; dừng bước.
- **FR-006**: Giỏ là mảng theo thứ tự nhặt (cuối = mới nhất, LIFO), sức chứa `hold_capacity`.
- **FR-007**: `interact`: trong bến → `gather_end("docked")` (xét trước); ngược lại, chỉ ở mặt nước, hái nút `ready` gần nhất trong `interact_radius` (hòa → id nhỏ) → `gather` hoặc `hold_full`.
- **FR-008**: Nút hái xong đặt `regrow_ticks = regrow_s·60`; đếm về 0 → `node_regrown`.
- **FR-009**: `catch`: chỉ dưới nước và `catch_cd_ticks = 0`, đàn cá gần nhất trong `catch_radius` (hòa → id nhỏ) → `fish_caught` (+`fish_yield[kind]`) hoặc `hold_full`; bắt thành công đặt hồi chiêu.
- **FR-010**: Hết giờ (`time_left_ticks = 0`) → `gather_end("time")`, giỏ giữ nguyên.
- **FR-011**: File kho ghi đúng một lần khi có `gather_end`, schema `{"items":{kind:n}}` (bỏ 0, sắp id); không ghi khi `tick_limit`.
- **FR-012**: Thứ tự một bước gather: (1) đồng hồ, bộ đếm, mọc lại → (2) bơi + chặn mép → (3) dive/surface, oxy, ngạt, ngất → (4) interact: bến rồi hái → (5) catch → (6) hết giờ.

### Functional Requirements — quan

- **FR-013**: Kho nạp từ `--inventory` hoặc `scenario.stock` (không cả hai, mã 2).
- **FR-014**: Lượt khách ở tick `120 + 900·k` (k ≥ 0) = `first_customer_tick + k·customer_interval_s·60` (đã xác nhận bởi TICKET-02); cần bàn trống (ghế id nhỏ nhất) và có món nấu được từ (kho − giữ chỗ), không thì `no_dish` (hết bàn → không khách). Khách ghi `order_tick` = tick gọi món.
- **FR-015**: Chọn món: chọn **đều theo seed** trong các món nấu được (đã xác nhận bởi TICKET-02), qua `Streams.get("quan_order")` trên danh sách món sắp theo id (tên luồng GIẢ ĐỊNH); giữ chỗ nguyên liệu ngay khi khách ngồi; cấp id khách bằng `IdAllocator`.
- **FR-016**: Kiên nhẫn `patience_s·60` giảm 1/tick khi khách chờ (chưa được phục vụ); về 0 khi ca còn giờ → `customer_left`, uy tín += `left_reputation_delta` (đã xác nhận bởi TICKET-02), nhả giữ chỗ chưa nấu, bàn trống.
- **FR-017**: Mỗi tick tối đa MỘT `interact`, chọn đối tượng trong `interact_radius` theo (khoảng cách, bếp trước bàn, id).
- **FR-018**: Bếp `idle` + tay rỗng + có khách chờ mà món chưa nấu/chưa được bưng → `cook_started` cho đơn `reserved` cũ nhất theo `order_tick` rồi id bàn (đã xác nhận bởi TICKET-02), trừ kho; `cook_s·60` tick → `dish_ready`; bếp `ready` + tay rỗng → `dish_picked` (tay ≤ `carry_limit`).
- **FR-019**: Tay cầm món khớp khách chờ ở bàn → `served`, khách `eating` `eat_s·60` tick → `paid` {price, tip}; tiền vào `money`, `earned`, `shift_earned`.
- **FR-020**: Boa nếu kiên nhẫn còn lại / kiên nhẫn đầy ≥ `tip_min_patience_ratio` lúc `served`: `tip = floor(price·tip_rate)`; boa dương → uy tín += `tip_reputation` (đã xác nhận bởi TICKET-02). Uy tín luôn kẹp [`reputation_min`, `reputation_max`].
- **FR-021**: Hết giờ → đóng ca: khách đang ăn trả ngay (`paid`), khách đang chờ rời không trừ uy tín, dọn món + giữ chỗ (đã xác nhận bởi TICKET-02); rồi `quan_end` reason `time` (money, earned, shift_earned, reputation). Thứ tự event lúc đóng ca: GIẢ ĐỊNH theo id khách, `paid` trước `quan_end`.
- **FR-022**: Thứ tự một bước quan: (1) đồng hồ, kiên nhẫn, nấu, ăn (theo id) → (2) đi lại → (3) một interact → (4) khách mới theo lịch → (5) hết giờ.
- **FR-023**: Scenario quan dựng sẵn `customers[]`, `stoves`, `hand`; mâu thuẫn mức luật → mã 2.

### Functional Requirements — chung

- **FR-024**: Số liệu chỉ đọc từ `game.contract.json`; ngẫu nhiên chỉ qua `Streams`; danh sách sắp theo id; không đồng hồ hệ thống.
- **FR-025**: Cùng đầu vào → JSONL, file kho giống từng byte.
- **FR-026**: Snapshot giữ các trường hiện có của starter (UI đọc); trường mới chỉ thêm, không đổi tên. `customers[]` xuất tập trường cố định (không lộ trường lạ từ scenario); uy tín làm tròn 6 chữ số sau mỗi thay đổi.

### Acceptance Criteria (kiểm chứng qua headless JSONL)

| AC | Nội dung | FR | Cách kiểm (headless) |
|---|---|---|---|
| AC-P1-01 | Dưới nước oxy −1/tick; mặt nước +refill, kẹp max | FR-001 | scenario `pos` d=10 / d=0, 60 tick; so `player.oxygen_ticks` |
| AC-P1-02 | `dive`/`surface` đúng một lần mỗi lần qua ranh giới | FR-002 | inputs `move [0,1]` rồi `[0,-1]`; đếm sự kiện |
| AC-P1-03 | `oxygen_empty` đúng một lần khi oxy về 0 | FR-003 | `oxygen_ticks:1` dưới nước, 2 tick |
| AC-P1-04 | Ngạt: −1 Máu mỗi `choke_interval_ticks` ở oxy 0 (tính cả bước chạm 0); oxy > 0 hoặc lên mặt nước reset | FR-004 | `oxygen_ticks:0`, 120 tick → 2 `choke`, `hp` 1 |
| AC-P1-05 | Máu 0 → `faint` + `gather_end fainted` + kho `{}` | FR-005, FR-011 | `hp:1, zero_oxy_ticks:59`, `--inventory-out` |
| AC-P1-06 | Hái nút ở mặt nước: `gather`, giỏ +1 cuối mảng, nút mọc lại sau `regrow_s` (`node_regrown`) | FR-007, FR-008 | nút cạnh người chơi, `interact`, 1200+ tick |
| AC-P1-07 | Không hái khi dưới nước; không bắt khi ở mặt nước | FR-007, FR-009 | inputs sai vùng → không sự kiện, giỏ không đổi |
| AC-P1-08 | Bắt cá: `fish_caught`, +`fish_yield[kind]`, hồi chiêu chặn bắt liên tiếp | FR-009 | `catch` hai tick liên tiếp → 1 `fish_caught` |
| AC-P1-09 | Giỏ đầy/không đủ chỗ → `hold_full`, giỏ ≤ 12, không đổi | FR-006 | `hold` 12 món (hoặc 10 + `ca_linh`) |
| AC-P1-10 | Hòa khoảng cách → id nhỏ | FR-007, FR-009 | 2 nút cách đều |
| AC-P1-11 | Bến xét trước hái → `gather_end docked` | FR-007 | trong bến + nút trong tầm |
| AC-P1-12 | Hết giờ → `gather_end time`, giữ giỏ; `tick_limit` không ghi kho | FR-010, FR-011 | smoke có sẵn |
| AC-P1-13 | Kho nối gather → quan đúng nội dung | FR-011, FR-013 | smoke `test_inv_01_*` |
| AC-P1-14 | Khách đến đúng lịch, ngồi bàn trống, giữ chỗ nguyên liệu | FR-014, FR-015 | stock đủ, tick 120 → `customer_arrived`; snapshot `customers[].reserved` |
| AC-P1-15 | Không món nấu được → `no_dish` | FR-014 | stock rỗng → `no_dish` ở tick 120 |
| AC-P1-16 | Hết kiên nhẫn → `customer_left`, uy tín −0.5, bàn trống | FR-016, FR-020 | stock đủ, không input, tick 120+3600 |
| AC-P1-17 | Nấu: `cook_started` (trừ kho) → `dish_ready` sau `cook_s` → `dish_picked` | FR-018 | scenario khách chờ + người chơi cạnh bếp, `interact` |
| AC-P1-18 | Phục vụ: `served` → sau `eat_s` `paid`; money/earned/shift_earned += price+tip | FR-019 | scenario `hand` + khách chờ cạnh bàn |
| AC-P1-19 | Boa `floor(giá·0.2)` + uy tín +0.2 khi kiên nhẫn ≥ 50% lúc giao; không boa khi < 50%; uy tín kẹp [0,5] | FR-020 | hai scenario kiên nhẫn khác nhau |
| AC-P1-20 | Một interact/tick, ưu tiên (khoảng cách, bếp trước bàn, id) | FR-017 | bếp và bàn cách đều |
| AC-P1-21 | Hết giờ quán → đóng ca (khách ăn trả ngay, khách chờ rời không trừ uy tín) → `quan_end time` + dòng `end` | FR-021 | `time_left_ticks:3` + khách `eating`/`waiting` dựng sẵn |
| AC-P1-24 | Bếp chọn đơn theo `order_tick` rồi id bàn | FR-018 | 2 khách chờ (T2 gọi trước T1) → `cook_started.customer_id` là khách T2 |
| AC-P1-22 | Tất định: hai lần chạy cùng seed/input → JSONL + kho giống từng byte (gather và quan) | FR-024, FR-025 | `cmp` |
| AC-P1-23 | Scenario mâu thuẫn mức luật → mã 2, không ghi đầu ra | FR-023 | khách giữ chỗ vượt kho |

### Key Entities

- **Người chơi (gather)**: pos [x,d], vel, heading, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks.
- **Giỏ (hold)**: mảng id nguyên liệu theo thứ tự nhặt, ≤ 12.
- **Nút hái**: id, kind (`bong_dien_dien`/`bong_sung`), pos (d=0), regrow_ticks.
- **Đàn cá**: id, kind (`ca_linh`/`ca_loc`), pos (dưới nước), đứng yên ở Phase 1.
- **Kho (inventory)**: `{"items":{kind:n}}` — cầu nối gather → quan.
- **Khách**: id, table_id, state (`waiting`/`eating`), dish_id, order_tick, patience_ticks_left, reserved, eat_ticks_left, price, tip — tập trường cố định (tên khớp HUD).
- **Bếp**: id, pos, state (`idle`/`cooking`/`ready`), dish, customer_id, cook_ticks_left.
- **Bàn**: id, pos, customer_id. **Tay (hand)**: null hoặc id món.
- **Món (menu)**: recipe, cook_s, price.

## Success Criteria *(mandatory)*

- **SC-001**: 100% AC-P1-01…24 có ít nhất một test/scenario headless và xanh trước tag `phase-1`.
- **SC-002**: Smoke test hiện có (`tests/test_smoke_p1.py`) vẫn xanh.
- **SC-003**: Một ngày chơi đủ (gather → kho → quan) chạy headless < 5 s mỗi buổi 10 800 tick.
- **SC-004**: 10/10 lần chạy lặp cùng seed cho JSONL giống từng byte.
- **SC-005**: Người chơi thử trên live hoàn thành một vòng hái → nấu → phục vụ → nhận tiền mà không cần đọc code.

## Clarifications

### Session 2026-11-21 (tự trả lời bằng giả định — PO chưa xác nhận, xem `docs/clarify.md` #12–#21 và Q-A…Q-F của `docs/research/phase-1.md` mục 7)

- Đã có căn cứ trong code (không còn là giả định): clarify #1 hết giờ giữ giỏ (`test_smoke_p1` có test), #2 ngất → kho `{}` (docstring gather), #3 oxy theo `d` cuối bước, dưới nước khi `d > surface_depth`, #7 hòa → id nhỏ; #4 phần reset (`scenario.py`: `zero_oxy_ticks ∈ [0,59]`, reset khi lên mặt nước).
- Q: Tick oxy chạm 0 có tính tick ngạt #1? (Q-A) → A: có (đã xác nhận bởi TICKET-02).
- Q: Bấm `catch` hụt / `hold_full` có hồi chiêu? (Q-B) → A: không, chỉ khi bắt thành công (đã xác nhận bởi TICKET-02).
- Q: Cập bến khi dưới nước? (Q-C) → A: giữ hành vi khung: được, chỉ xét bán kính.
- Q: Lịch khách khi scenario đặt `time_left_ticks`? (Q-E) → A: tick 120 + 900·k (đã xác nhận bởi TICKET-02); đếm theo `phase_tick`/`self.tick` từ đầu lượt chạy (cách đếm khi scenario rút ngắn giờ: GIẢ ĐỊNH).

- Q: Ngạt đếm thế nào? → A: chỉ đếm khi oxy 0 **và** dưới nước, tính cả bước chạm 0; đủ 60 → −1 Máu, đếm lại 0; reset khi oxy > 0 hoặc lên mặt nước (đã xác nhận bởi TICKET-02).
- Q: Không đủ chỗ cho cả lượt nhặt (vd. `ca_linh` yield 3, còn 1 chỗ)? → A: (đã xác nhận bởi TICKET-02) không nhặt gì, phát `hold_full`, không đặt hồi chiêu.
- Q: Bắt xong đàn cá còn không? → A: GIẢ ĐỊNH (clarify #14, đổi so với bản trước): đàn bị bắt bị loại; Phase 2 có cá bơi/sinh thêm.
- Q: `invuln_ticks` dùng làm gì ở Phase 1? → A: GIẢ ĐỊNH: chỉ đếm ngược (đã có), không ảnh hưởng luật Phase 1.
- Q: Khách chọn món? → A: chọn đều theo seed trong các món nấu được (đã xác nhận bởi TICKET-02); luồng `Streams.get("quan_order")` (GIẢ ĐỊNH tên).
- Q: Bàn đầy khi tới lượt khách? → A: không có khách (đã xác nhận bởi TICKET-02); không phát sự kiện (GIẢ ĐỊNH); lịch tiếp tục.
- Q: Boa làm tròn? → A: `floor(giá × 0.2)`, KHÔNG `round` (giả định cũ sai); tỉ lệ kiên nhẫn tính lúc giao (`served`) (đã xác nhận bởi TICKET-02).
- Q: Bếp nấu món cho ai? → A: đơn `reserved` cũ nhất theo `order_tick` rồi id bàn (giả định cũ "id khách nhỏ nhất" sai) (đã xác nhận bởi TICKET-02); bếp ghi `customer_id`.
- Q: Kiên nhẫn có giảm khi món đang nấu? → A: GIẢ ĐỊNH: có, giảm tới lúc `served`.
- Q: Khách bỏ đi khi món đã nấu? → A: GIẢ ĐỊNH: nguyên liệu đã trừ không hoàn; món trên bếp/tay vẫn còn và có thể phục vụ khách sau cùng món.
- Q: Sau `paid` khách? → A: GIẢ ĐỊNH: rời ngay, bàn trống, khách xóa khỏi `customers`.

## Assumptions

- Thứ tự bước (FR-012, FR-022) theo `TODO(nhóm)` của starter; PRD-0 mục 13.8 / mục F chưa đọc được — cần PO đối chiếu.
- Tên sự kiện quan lấy từ HUD `chonoi/web/index.html`; `data` của từng sự kiện là đề xuất trong `contracts/events.md` (GIẢ ĐỊNH, Q-D) — TV1/TV5 chốt ở `docs/contracts/`.
- Nguồn bổ sung: `docs/research/phase-1.md` (bản đồ TODO, Test Contract, edge case tick).
- `first_customer_tick` đơn vị tick; các `*_s` nhân `tick_hz`.
- Không có đồ họa/sáng tạo ở Phase 1; chế độ `day` ngoài phạm vi.
- Khung `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` giữ nguyên; riêng `scenario.py` có `TODO(nhóm)` kiểm mâu thuẫn mức luật (cần nhóm đồng ý sửa).
