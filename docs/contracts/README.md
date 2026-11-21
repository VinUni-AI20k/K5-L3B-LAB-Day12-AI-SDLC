# Hợp đồng tích hợp — Phase 1 (contract v1.0)

> Chốt ở kickoff 1.1 bởi PO (HoangHongNgo). Đổi gì ở file này: báo cả nhóm trước, ghi lý do trong commit (hoặc ADR ở `docs/adr/`).
> Nguồn: PRD-0 (mục D, E, F, G), code khung `chonoi/`, `docs/plan/phase-1.md`. Mục nào ghi **[giả định]** là nhóm tự chốt khi PRD chưa nói rõ; câu hỏi tương ứng nằm ở [`docs/clarify.md`](../clarify.md). Có câu trả lời khác thì sửa đúng dòng đó.

Số liệu (bán kính, thời gian, giá…) **không** chép vào đây: luôn đọc `game.contract.json` → `tuning`.

---

## 1. Schema file kho (PRD-0 mục G)

```json
{"items": {"<kind>": <số nguyên ≥ 0>, ...}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items` (object). Khóa khác → mã 2. |
| `kind` hợp lệ (P1) | `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung` (`chonoi/inventory.py:KINDS_P1`). Kind lạ → mã 2. |
| Số lượng | Số nguyên ≥ 0, không phải bool. Âm/thực/bool → mã 2. Mục bằng 0 được đọc nhưng bị bỏ. |
| Ghi (gather) | Ghi **đúng một lần** khi có `gather_end` (`docked`, `time`, `fainted`). Chạm `--ticks` trước khi kết thúc → **không** ghi, file đích giữ nguyên. |
| Định dạng ghi | Khóa sắp theo id nguyên liệu, bỏ mục 0, JSON gọn `(",", ":")`, UTF-8, kết thúc `\n`, ghi nguyên tử (file tạm + `os.replace`). |
| Nội dung | `items` = đếm từ giỏ `hold` lúc kết thúc. `fainted` → `{"items":{}}`. |
| Đọc (quan) | `--inventory kho.json` nạp vào `stock`. Không được vừa có `--inventory` vừa có `quan.stock` trong scenario (mã 2). |

Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`.
Đã kiểm: `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/contracts/inventory.sample.json --out q.jsonl` → mã 0, snapshot tick 0 có `"stock":{"bong_sung":2,"ca_loc":1}`.

---

## 2. Dòng JSONL và event (PRD-0 mục E)

Mỗi event là một dòng `{"type":"event","tick":k+1,"phase":"gather|quan","name":...,"data":{...}}` (runner lo vỏ; sim chỉ trả `(name, data)`). Trong một bước, event xếp **theo thứ tự xử lý** trong `step()`; nhiều thực thể cùng loại thì theo `sort_by_id`. Vị trí là mảng 2 số `[x, d]` / `[x, z]`.

### 2.1 Gather — `GatherSim.step` (thứ tự bước)

| # bước | Event | `data` | Ai phát (lát) | Ai nghe |
|---|---|---|---|---|
| 1 | `node_regrown` | `{"node_id"}` | khung (có sẵn) | UI, test |
| 2 | `dive` | `{"pos"}` — pos cuối bước | lát 1 | UI, test |
| 2 | `surface` | `{"pos"}` — pos cuối bước | lát 1 | UI, test |
| 2 | `oxygen_empty` | `{}` **[giả định]** | lát 1 | UI (cảnh báo), test |
| 2 | `choke` | `{"hp"}` — Máu sau khi trừ | lát 1 | UI, test |
| 2 | `faint` | `{"cause":"choke","lost":[kind…],"hp":0}` — `lost` theo LIFO (mới nhất trước) | lát 1 | UI, test |
| 3 | `gather` | `{"node_id","kind","count"}` **[giả định `kind`,`count`]**; `count` = `node_yield` | lát 2 | UI, test |
| 3/4 | `hold_full` | `{"action":"gather"\|"catch","node_id"\|"fish_id","required","free"}` | lát 2 | UI, test |
| 4 | `fish_caught` | `{"fish_id","kind","count"}` **[giả định]**; `count` = `fish_yield[kind]` | lát 2 | UI, test |
| 3/5, hoặc 2 khi ngất | `gather_end` | `{"reason":"docked"\|"time"\|"fainted","inventory":{"items":{…}}}` | khung + lát 1 (`fainted`) | runner (ghi kho), UI |

Thứ tự trong một bước (khung đã đặt sẵn trong `step()`): 1 đồng hồ/hồi chiêu/mọc lại → 2 bơi + chặn mép → dive/surface → oxy/ngạt/ngất → 3 `interact` (bến **trước**, rồi hái) → 4 `catch` → 5 hết giờ.

### 2.2 Quán — `QuanSim.step`

`order_id` **= id khách** (mỗi khách đúng một đơn ở P1) **[giả định]**.

| Event | `data` | Ai phát (lát) |
|---|---|---|
| `customer_arrived` | `{"customer_id","table_id","dish_id","reserved":{kind:n}}` **[giả định]** | lát 3 |
| `no_dish` | `{"table_id"}` **[giả định]** — có bàn trống nhưng không món nào đủ kho khả dụng | lát 3 |
| `customer_left` | `{"customer_id","table_id","reason":"patience"\|"closing"}` | lát 3 (patience), lát 4 (closing) |
| `cook_started` | `{"stove_id","order_id","dish_id","items":{kind:n} (sắp theo kind),"base_price"}` | lát 4 |
| `dish_ready` | `{"stove_id","order_id","dish_id"}` | lát 4 |
| `dish_picked` | `{"stove_id","order_id","dish_id"}` | lát 4 |
| `served` | `{"table_id","customer_id","order_id","dish_id","tip"}` | lát 4 |
| `paid` | `{"customer_id","order_id","amount","tip","reason":"finished_eating"\|"closing"}` — `amount` = `base_price + tip` | lát 4 |
| `quan_end` | `{"reason":"time","money","earned","shift_earned","reputation"}` | khung + lát 4 |

Cuối ca (lát 4): khách đang ăn → `paid` `closing`; khách đang chờ → `customer_left` `closing` (không trừ uy tín); rồi `quan_end`. Điểm = `earned + reputation_multiplier × floor(reputation)` (runner đã tính).

---

## 3. Cấu trúc khách / đơn (chốt giữa lát 3 ↔ lát 4)

Mỗi phần tử `QuanSim.customers` (snapshot in ra nguyên, sắp theo id):

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | str | id khách = `order_id` (cấp qua `IdAllocator`) |
| `table_id` | str | bàn đang ngồi |
| `dish_id` | str | khóa trong `tuning.menu` |
| `order_tick` | int | `phase_tick` lúc đến (để lấy đơn cũ nhất) |
| `state` | `"waiting"` \| `"eating"` | |
| `patience_ticks_left` | int | `patience_s × 60` lúc đến; giảm từ bước sau khi đến |
| `eat_ticks_left` | int | 0 khi chờ; `eat_s × 60` khi `served` |
| `order_status` | `"reserved"` \| `"cooking"` \| `"ready"` \| `"carried"` \| `"served"` | |
| `reserved` | `{kind:n}` | nguyên liệu đang giữ; rỗng sau `cook_started` |
| `base_price` | int \| null | chốt ở `cook_started` |
| `tip` | int | 0 cho tới `served` |

Kho khả dụng = `stock[kind] − Σ reserved[kind]`. `hand` = `null` hoặc `{"order_id","dish_id"}`. Bếp: `state` `"idle"|"cooking"|"ready"`, `dish` = `null` hoặc `{"order_id","dish_id"}`.

---

## 4. Giao diện sim ↔ UI (`chonoi/live.py`, `chonoi/web/index.html`)

UI **chỉ đọc** snapshot, **chỉ gửi** input. Không gọi hàm luật, không sửa state.

**Lệnh UI gửi** — `POST /input`: `{"move":[a,b], "interact":bool, "catch":bool}` (trạng thái phím đang giữ; `LiveInputs` tự lấy cạnh lên). `move` mỗi thành phần ∈ [−1, 1], chuẩn hóa nếu dài > 1. Gather: `[x, d]` (d dương = lặn xuống); quán: `[x, z]`.

**UI đọc** — `GET /state` = snapshot (cùng trường headless) + `meta` + `events`.

| Phần | Trường UI dùng cho HUD |
|---|---|
| Chung | `mode`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score` |
| Gather | `player.{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold` (thứ tự nhặt), `hold_count`, `hold_capacity`, `nodes[].{id,pos,kind,ready,regrow_ticks}`, `fish[].{id,pos,kind,heading_deg}` |
| Quán | `player.pos`, `stock` (tồn, >0), `hand`, `stoves[].{id,pos,state,dish,cook_ticks_left,ready_ticks}`, `tables[].{id,pos,customer_id}`, `customers[]` (mục 3) |

UI tự tính "kho khả dụng" từ `stock` − `customers[].reserved`, không cần trường riêng. Sim thêm trường mới không làm vỡ UI (UI bỏ qua trường chưa biết).

---

## 5. Ranh giới file (ai sửa đâu)

| Lát | Người | Được sửa |
|---|---|---|
| 1 | ChuTungDuongg | `GatherSim.step` bước 2 (dive/surface, oxy, ngạt, ngất) + `_update_oxygen`; `tests/test_p1_lat1.py` |
| 2 | haiquanng | `GatherSim.step` bước 3–4 (hái, bắt cá) + `_add_to_hold`; `tests/test_p1_lat2.py` |
| 3 | minhphuong150505 | `QuanSim`: dựng khách, lịch khách, chọn món, giữ chỗ, kiên nhẫn; `_validate_quan` trong `chonoi/scenario.py`; `tests/test_p1_lat3.py` |
| 4 | phuthaitran | `QuanSim`: chọn interact, bếp, bưng, phục vụ, ăn/trả tiền, cuối ca; `tests/test_p1_lat4.py`, `tests/fixtures/quan_*.json` |
| HUD | RachalHys | `chonoi/web/`, `README.md`, `docs/verification/` |
| PO | HoangHongNgo | `docs/contracts/`, `game.contract.json`, `chonoi/contract.py`, `docs/clarify.md` |

Hàm dùng chung giỏ (lát 2 viết, lát 1 dùng): `_add_to_hold(kinds: list[str]) -> bool` — thêm đủ cả `kinds` theo thứ tự nếu `len(hold) + len(kinds) ≤ hold_capacity`, ngược lại không thêm gì và trả `False`. Ngất bỏ giỏ theo LIFO: `lost = list(reversed(hold))`.
