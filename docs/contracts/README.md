# Hợp đồng tích hợp — Phase 1 (chốt phút 15)

> Chủ hợp đồng: **Diệp (Integrator)**. Đổi bất kỳ tên trường / sự kiện nào ở đây: báo cả nhóm trong kênh chat **trước**, sửa file này cùng commit với code, ghi lý do (ADR hoặc dòng "Lịch sử thay đổi" cuối file).
>
> Nguồn: khung starter (`chonoi/runner.py`, `inventory.py`, `sim/*.py`, `live.py`), Test Contract v1.0 trong PRD-0 và tên trường HUD đang dùng (`chonoi/web/index.html`). Những mục ghi **[GĐ]** là giả định của nhóm; PO (Minh) xác nhận với PRD-0 rồi ghi vào `docs/clarify.md`.

Quy ước chung:
- Thời gian luôn tính bằng **tick** (60 tick/s). Trường đếm ngược có hậu tố `_ticks_left`. Số giây trong `game.contract.json` đổi ra tick bằng `round(s × 60)`.
- Id: nguyên liệu/món dùng id trong `game.contract.json` (`ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`; `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`). Bếp `B*`, bàn `T*`, nút `N*`, cá `F*`, khách `C*` (cấp bằng `IdAllocator`, không trùng fixture).
- Mọi mảng thực thể trong snapshot sắp bằng `ids.sort_by_id`. Object đếm (`stock`, `items`, `reserved`) sắp theo khóa, bỏ mục bằng 0.
- Tiền là số nguyên (đơn vị nghìn đồng). Uy tín là số thực, kẹp `[reputation_min, reputation_max]`.

---

## 1. File kho (gather → quan)

**Schema (Contract G, v1.0):**

```json
{"items": {"<id nguyên liệu>": <số nguyên ≥ 1>, ...}}
```

| Quy tắc | Ai lo |
|---|---|
| Khóa gốc **chỉ** có `items`; id phải thuộc `KINDS_P1`; số nguyên ≥ 0 (không bool, không âm). Sai → `BadInput` → mã thoát 2 | `chonoi/inventory.py:read_inventory` (khung) |
| Ghi: bỏ mục 0, sắp khóa, JSON gọn `separators=(",", ":")`, UTF-8, kết thúc `\n`, ghi qua file tạm rồi `os.replace` | `inventory.py:write_inventory` (khung) |
| Ghi **đúng một lần**, chỉ khi có `gather_end` (cả `docked`, `time`, `fainted`); chưa kết thúc → giữ nguyên file đích | `runner.Session.write_inventory_if_done` (khung) |
| Nội dung file = `gather_end.data.inventory` = `hold_to_items(hold)`; `fainted` → `{"items":{}}` | Lát 1 (Hưng: giỏ, ngất), Lát 2 (Phát: hái/bắt) |
| Quan nạp bằng `--inventory` **hoặc** `scenario.quan.stock` (có cả hai → mã 2); thành `self.stock` (tồn vật lý) | Khung + Lát 3 (Minh) |

File mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json) — `{"items":{"bong_sung":2,"ca_loc":1}}` (đủ nấu `goi_bong_sung` hoặc `ca_loc_nuong_trui`).

**API giỏ giữa Lát 1 ↔ Lát 2** (chốt để hai người không giẫm nhau trong `gather.py`):
- `self.hold: list[str]` — thứ tự nhặt, phần tử cuối là mới nhất (bỏ LIFO khi ngất).
- `self._hold_free() -> int` = `hold_capacity - len(self.hold)` (Hưng viết).
- `self._hold_add(kind, n) -> bool` — đủ chỗ thì thêm `n` phần tử `kind` và trả `True`; không đủ thì **không thêm gì**, trả `False` để người gọi phát `hold_full` (Hưng viết, Phát gọi).

---

## 2. Giao diện sim ↔ UI

UI (`chonoi/web/index.html`, `chonoi/live.py`) **chỉ đọc** snapshot và **chỉ gửi** input. UI không bao giờ tự tính luật làm thay đổi trạng thái (gợi ý "E: nấu…" chỉ là hiển thị).

### 2.1 UI gửi vào (lệnh)

| Kênh | Nội dung |
|---|---|
| `POST /input` | `{"move": [a, b], "interact": bool, "catch": bool}` — trạng thái phím **đang giữ**; `move` là `[x, d]` (gather) hoặc `[x, z]` (quan), mỗi số ∈ [-1, 1], sim chuẩn hóa độ dài ≤ 1 |
| `POST /restart` | chơi lại cùng seed, cùng scenario |
| Headless | file `--inputs` (`{"frames":[{"tick","move","interact","catch"}]}`), trường vắng kế thừa frame trước |

Sim chỉ phản ứng ở **cạnh lên** của `interact`/`catch` (`inp.pressed(...)`). Quan: mỗi bước **tối đa một** interact.

### 2.2 UI đọc ra (`GET /state` = dòng snapshot headless + `meta` + `menu` + `events`)

**Trường chung** (do `runner._common` lo, mọi mode): `type, tick, sim_tick, mode, phase, phase_tick, state ("playing"|"finished"), time_left_ticks, money, earned, reputation, score`; `score = earned + reputation_multiplier × floor(reputation)`.
Chỉ ở live: `meta` = `tuning[mode]`, `menu` = `tuning.menu`, `events` = các dòng event gần nhất.

**Gather** (`GatherSim.snapshot`, khung đã có đủ — lát 1/2 chỉ cập nhật giá trị):

| Trường | Kiểu | Ai cập nhật |
|---|---|---|
| `player.pos [x,d]`, `vel`, `heading_deg` | số | khung |
| `player.oxygen_ticks`, `oxygen_max_ticks`, `zero_oxy_ticks`, `at_surface` | int / bool | Lát 1 |
| `player.hp`, `hp_max`, `invuln_ticks` | int | Lát 1 |
| `player.catch_cd_ticks` | int | Lát 2 |
| `hold [kind…]`, `hold_count`, `hold_capacity` | mảng / int | Lát 1 (thêm/bỏ), Lát 2 (gọi thêm) |
| `nodes[] {id, pos, kind, ready, regrow_ticks}` | | Lát 2 |
| `fish[] {id, pos, kind, heading_deg}` | | Lát 2 |

**Quan** (`QuanSim.snapshot`):

| Trường | Kiểu / giá trị | Ai cập nhật |
|---|---|---|
| `player.pos [x,z]` | số | khung |
| `stock {kind: n}` | **tồn vật lý** (chưa trừ giữ chỗ). Kho khả dụng = `stock − Σ reserved` của khách `order_status == "reserved"` | Lát 3 (không trừ khi giữ chỗ), Lát 4 (trừ khi bắt đầu nấu) |
| `hand` | `null` hoặc `{"order_id": str, "dish_id": str, "base_price": int}`; `order_id` = id khách | Lát 4 |
| `stoves[] {id, pos, state, dish, cook_ticks_left, ready_ticks}` | `state ∈ idle / cooking / ready`; `dish` = `null` hoặc `{"dish_id": str, "order_id": str}`; `ready_ticks` = số tick đã chín (dùng khi `burn_s` khác null, P1 = null) | Lát 4 |
| `tables[] {id, pos, customer_id}` | `customer_id` = khách đang ngồi hoặc `null` | khung (suy từ `customers`) |
| `customers[]` | xem bảng dưới | Lát 3 tạo/bỏ, Lát 4 đổi trạng thái |

**Trường của một khách** (Lát 3 ↔ Lát 4 cùng dùng; scenario `quan.customers[]` dùng **cùng tên**):

| Trường | Kiểu | Ý nghĩa | Ghi bởi |
|---|---|---|---|
| `id` | `"C…"` | id khách = id đơn (1 khách 1 món) | Lát 3 |
| `table_id` | `"T…"` | bàn trống id nhỏ nhất lúc đến | Lát 3 |
| `dish_id` | id món | món đã chọn (đều theo seed trong các món đủ kho khả dụng) | Lát 3 |
| `state` | `"waiting"` \| `"eating"` | chờ món / đang ăn | Lát 3 (`waiting`), Lát 4 (`eating`) |
| `order_status` | `"reserved"` \| `"assigned"` \| `"served"` (\| `"unfulfillable"` dự phòng fixture) | đã giữ nguyên liệu / đã vào bếp (đang nấu, chín, trên tay) / đã dọn | Lát 3 (`reserved`), Lát 4 (còn lại) |
| `reserved` | `{kind: n}` | nguyên liệu đang giữ; = công thức khi `reserved`, `{}` từ lúc `cook_started` | Lát 3 đặt, Lát 4 xóa |
| `order_tick` | int | tick đặt món — Lát 4 lấy đơn `reserved` **cũ nhất** theo (`order_tick`, `id`) | Lát 3 |
| `patience_ticks_left` | int | `patience_s × 60` lúc đến, giảm từ **bước sau**; dừng khi `eating`; về 0 → `customer_left` patience | Lát 3 |
| `eat_ticks_left` | int | `eat_s × 60` lúc `served`, về 0 → `paid` | Lát 4 |
| `base_price` | int | giá món (PRD-0 mục D), đặt lúc khách đến; `hand.base_price` mang theo khi bưng | Lát 3 đặt, Lát 4 dùng |
| `tip` | int | `floor(base_price × tip_rate)` nếu `patience_ticks_left / (patience_s×60) ≥ tip_min_patience_ratio`, ngược lại 0; đặt khi `served` | Lát 4 |

Scenario thiếu `reserved` cho khách `order_status == "reserved"` → Lát 3 **suy ra** = công thức `dish_id` (clarify #5). Khách `eating` thiếu `base_price`/`tip`/`eat_ticks_left`, hoặc tổng giữ chỗ vượt `stock` → mã 2 (Khang thêm vào `scenario.py`).

**Ranh giới hàm trong `quan.py`** (tránh xung đột gộp): Lát 3 viết `_tick_customers()`, `_spawn_customer()`, `_leave(c, reason)`, `_available()`; Lát 4 viết `_tick_stoves()`, `_tick_eating()`, `_interact()`, `_cook()`, `_pick()`, `_serve()`, `_pay()`, `_rep(delta)`. `step()` chỉ gọi các hàm này theo thứ tự PRD-0 mục F (Diệp gộp).

---

## 3. Danh sách sự kiện

Dòng JSONL: `{"type":"event","tick":k+1,"phase":…,"name":…,"data":{…}}`. Sim **phát** (trả list `(name, data)` từ `step`, đúng thứ tự xử lý trong bước); runner ghi JSONL; **nghe**: UI (toast + nhật ký, `eventText`), QA (`tests/`, `helpers.events`), runner (chỉ `gather_end` → ghi kho). Khóa trong `data` không đổi tên tùy tiện — UI và test đọc đúng tên này.

### Gather

| Sự kiện | `data` | Phát bởi | Khi nào |
|---|---|---|---|
| `dive` | `{"pos":[x,d]}` | Lát 1 | đầu bước ở mặt nước (d ≤ `surface_depth`), cuối bước dưới nước |
| `surface` | `{"pos":[x,d]}` | Lát 1 | ngược lại của `dive` |
| `oxygen_empty` | `{}` | Lát 1 | oxy từ > 0 xuống 0 |
| `choke` | `{"hp": int}` | Lát 1 | đủ `choke_interval_ticks` tick ở oxy 0 dưới nước; `hp` = Máu **sau** khi trừ |
| `faint` | `{"lost":[kind…]}` | Lát 1 | Máu về 0; `lost` = giỏ bị bỏ theo LIFO (mới nhất trước) |
| `gather` | `{"node_id", "kind", "amount": int}` | Lát 2 | hái nút ready gần nhất (ở mặt nước, hòa theo id) |
| `node_regrown` | `{"node_id"}` | khung | `regrow_ticks` về 0 |
| `fish_caught` | `{"fish_id", "kind", "yield": int}` | Lát 2 | `catch` dưới nước, hết hồi chiêu, có đàn trong `catch_radius` |
| `hold_full` | `{"required": int, "free": int}` | Lát 2 | không đủ chỗ cho lượt hái/bắt (không thử đàn/nút khác) |
| `gather_end` | `{"reason": "docked"\|"time"\|"fainted", "inventory": {"items": {…}}}` | khung (`_finish`) + Lát 1 (fainted) | kết thúc buổi; luôn là sự kiện cuối |

### Quan

| Sự kiện | `data` | Phát bởi | Khi nào |
|---|---|---|---|
| `customer_arrived` | `{"customer_id", "table_id", "dish_id"}` | Lát 3 | khách đến theo lịch (`first_customer_tick`, rồi mỗi `customer_interval_s`), có bàn trống và có món đủ kho khả dụng; giữ chỗ ngay |
| `no_dish` | `{"table_id"}` | Lát 3 | đến lịch, có bàn trống nhưng không món nào đủ kho khả dụng → không tạo khách, không chiếm bàn (clarify #1) |
| `customer_left` | `{"customer_id", "table_id", "reason": "patience"\|"closing", "reputation": float}` | Lát 3 (Lát 4 cấp `_rep`) | hết kiên nhẫn (uy tín `+left_reputation_delta`) / hết ca; `reputation` = uy tín **sau** khi đổi; món của khách bị hủy, không hoàn nguyên liệu đã nấu (clarify #4) |
| `cook_started` | `{"stove_id", "customer_id", "dish_id"}` | Lát 4 | interact bếp `idle` + có đơn `reserved` cũ nhất; trừ `stock`, xóa `reserved` |
| `dish_ready` | `{"stove_id", "customer_id", "dish_id"}` | Lát 4 | `cook_ticks_left` về 0 → bếp `ready` |
| `dish_picked` | `{"stove_id", "customer_id", "dish_id"}` | Lát 4 | interact bếp `ready`, tay trống (`carry_limit` = 1) |
| `served` | `{"customer_id", "table_id", "dish_id", "tip": int}` | Lát 4 | interact bàn có khách `waiting` đúng `hand.order_id` |
| `paid` | `{"customer_id", "table_id", "amount": int, "tip": int, "money": int, "reputation": float}` | Lát 4 | `eat_ticks_left` về 0; `amount = base_price + tip`; `money` = tiền **sau** khi cộng; có boa → uy tín `+tip_reputation` **[GĐ, clarify #7]**; `reputation` = uy tín sau khi đổi; bàn được giải phóng |
| `quan_end` | `{"reason":"time", "money", "earned", "shift_earned", "reputation"}` | khung + Lát 4 | hết ca; luôn là sự kiện cuối (sau các `customer_left` closing) |

Thứ tự id trong một bước: nhiều thực thể cùng phát một loại sự kiện → theo `sort_by_id` (clarify #2).

---

## Lịch sử thay đổi

| Ngày | Ai | Thay đổi | Lý do |
|---|---|---|---|
| 21/11/2026 | Diệp | Bản chốt phút 15: kho, sim↔UI, sự kiện | Kickoff Phase 1 |
| 21/11/2026 | Minh | `hand` thêm `base_price`; bỏ [GĐ] cho `hand`/`stove.dish` | Đối chiếu PRD-0 mục D |
| 21/11/2026 | Diệp | `price` → `base_price`; ghi rõ luật boa/uy tín của `paid` | Khớp code lát 3 + lát 4 |
| 21/11/2026 | Diệp | Code lát 3 về đúng hợp đồng: snapshot `stock` = tồn vật lý; `no_dish` data `{table_id}`; `customer_left` thêm `reputation` | HUD của Nhài tự trừ giữ chỗ (bị trừ 2 lần) và đọc `customer_left.reputation` |
