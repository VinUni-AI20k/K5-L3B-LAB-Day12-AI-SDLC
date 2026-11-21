# Hợp đồng tích hợp — Contract v1.2 (Phase 3)

> **v1.2 THAY THẾ v1.0/v1.1** ở các mục đánh dấu [THAY THẾ] trong TICKET-03 ([`docs/prd/phase-3.md`](../prd/phase-3.md)): kho đếm → **kho cá thể** `{id, kind, fresh}`, giữ chỗ theo lượng → **theo id**, giá niêm yết → **giá theo tươi**, `items`/`lost` trong event là **mảng cá thể**, thêm luật **ươn** + event `spoiled`. Quyết định: [ADR-0001](../adr/0001-kho-ca-the-do-tuoi.md); thay đổi cụ thể: [CHANGELOG](../../CHANGELOG.md). Phần còn lại của file này (v1.0/v1.1) vẫn đúng nếu không mâu thuẫn với các mục dưới.

> Integrator giữ file này (NgChiVinh). Nguồn gốc: [`docs/prd/phase-1.md`](../prd/phase-1.md) mục D, E, F, G.
> **Đổi hợp đồng:** báo cả nhóm trong kênh, cần người giữ lát bị ảnh hưởng đồng ý, ghi lý do vào commit (hoặc ADR nếu lớn).

Mục lục: [1. File kho](#1-file-kho-gather--quan) · [2. Sự kiện](#2-danh-sách-sự-kiện) · [3. Sim ↔ UI](#3-giao-diện-sim--clientui) · [4. Quán: lát 3 ↔ lát 4](#4-hợp-đồng-nội-bộ-quán-lát-3--lát-4)

---

## 1. File kho (gather → quan)

**Schema** (máy đọc: [`inventory.schema.json`](inventory.schema.json)):

```json
{"items": [{"id": "<chuỗi khác rỗng, duy nhất>", "kind": "<kind>", "fresh": <số trong [0, 100]>}, ...]}   // v1.2
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Chỉ đúng một khóa `items`. Khóa khác → mã 2. |
| `kind` hợp lệ | `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo` (v1.1 thêm `ca_keo`, `keo_neo`). Kind lạ → mã 2. |
| Giá trị | Số nguyên ≥ 0 (không bool, không số thực). Âm → mã 2. |
| Bên ghi (gather) | v1.2: mảng cá thể sắp theo id, `fresh` float đầy đủ (không làm tròn); JSON gọn + xuống dòng; ghi file tạm cùng thư mục rồi `os.replace` (nguyên tử). Kho đếm v1.0/v1.1 → **mã 2**. |
| Khi nào ghi | Đúng **một lần** khi có `gather_end` (`docked` / `time` / `fainted`). Ngất → `{"items":[]}`. Chạm `--ticks` trước khi kết thúc → **không** tạo/ghi đè file. |
| Khớp event | Nội dung file == `gather_end.data.inventory`. |
| Bên đọc (quan) | `--inventory <file>` → `stock`. Không có cả `--inventory` lẫn `scenario.quan.stock` → kho rỗng. Có cả hai → mã 2. Trần giỏ (12) **không** áp lên kho quán. |

**Ví dụ hợp lệ (v1.2):** [`inventory.sample.json`](inventory.sample.json) → `{"items":[{"id":"I1","kind":"bong_sung","fresh":100},{"id":"I2","kind":"bong_sung","fresh":97.5},{"id":"I3","kind":"ca_loc","fresh":100}]}` · kho rỗng `{"items":[]}`.

**Ví dụ sai (mã 2, v1.2):** kho đếm `{"items":{"ca_loc":1}}` · kind lạ `{"items":[{"id":"I1","kind":"ca_la_lung","fresh":100}]}` · id trùng · `fresh` 101 / −1 / NaN · thiếu/thừa khóa.

Code: `chonoi/inventory.py` (`read_inventory`, `write_inventory`, `hold_to_items`) — khung đã làm, **không sửa** khi chưa báo Integrator.

**Smoke hai tiến trình** (QA chạy ở phút 25 và 45):

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
# kỳ vọng (v1.2): snapshot quán tick 0 có "stock" đúng id, kind, fresh như file kho (sau 1 bước hao ở gather)
```

---

## 2. Danh sách sự kiện

Dòng event: `{"type":"event","tick":k+1,"phase":"gather|quan","name":...,"data":{...}}`. Ghi theo **thứ tự xử lý** trong bước, rồi mới snapshot. **v1.2:** `cook_started.items` là mảng cá thể sắp kind rồi id; `lost` (`monster_hit`, `faint`) là mảng cá thể theo thứ tự bỏ LIFO. Event mới `spoiled {item_id, kind, location: hold|stock}`.

### Gather — `chonoi/sim/gather.py`

| name | data | Phát ở bước (mục F) | Lát / người | Ai nghe |
|---|---|---|---|---|
| `node_regrown` | `node_id` | 1 — nút về 0 (theo id) | khung (đã có) | UI, QA |
| `dive` | `pos` (sau di chuyển) | 2 — đổi từ mặt nước xuống dưới (d > 0.5) | Lát 1 · NgChiVinh | UI, QA |
| `surface` | `pos` | 2 — đổi từ dưới lên mặt (d ≤ 0.5) | Lát 1 · NgChiVinh | UI, QA |
| `oxygen_empty` | `oxygen_ticks: 0` | 2 — oxy từ dương xuống 0 | Lát 1 · NgChiVinh | UI, QA |
| `choke` | `hp` (sau trừ) | 2 — zero_oxy_ticks đủ 60 | Lát 1 · NgChiVinh | UI, QA |
| `faint` | `cause:"choke"`, `lost` (LIFO), `hp: 0` | 2 — Máu về 0 | Lát 1 · NgChiVinh | UI, QA |
| `gather` | `node_id`, `kind`, `amount` | 3 — hái thành công | Lát 2 · TrungHieuPh | UI, QA |
| `fish_caught` | `fish_id`, `kind`, `yield` | 4 — bắt thành công | Lát 2 · TrungHieuPh | UI, QA |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | 3 / 4 — thiếu chỗ | Lát 2 · TrungHieuPh | UI, QA |
| `gather_end` | `reason` (`docked`/`time`/`fainted`), `inventory` (theo §1) | 2 (`fainted`), 3 (`docked`), 5 (`time`) | khung + Lát 1 (`fainted`) | runner (ghi kho), UI, QA |

Thứ tự trong `faint`: bỏ giỏ theo LIFO → `faint` → `gather_end(fainted, inventory {"items":{}})` → dừng bước.

### Quán — `chonoi/sim/quan.py`

| name | data | Phát ở bước (mục F) | Lát / người | Ai nghe |
|---|---|---|---|---|
| `customer_arrived` | `order_id`, `table_id`, `dish_id` | 5 — đến lịch, có bàn, có món | Lát 3 · 22520160 | UI, QA |
| `no_dish` | `{}` | 5 — có bàn nhưng không món nào đủ nguyên liệu khả dụng | Lát 3 · 22520160 | UI, QA |
| `customer_left` (`reason:"patience"`) | `order_id`, `table_id`, `reason`, `reputation` (sau đổi) | 4 — kiên nhẫn 0, ca còn giờ | Lát 3 · 22520160 | UI, QA |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (sắp theo kind), `base_price` | 3 — interact bếp idle | Lát 4 · HoangQuan23112004 | UI, QA |
| `dish_ready` | `stove_id`, `order_id`, `dish_id` | 2 — nấu xong | Lát 4 · HoangQuan23112004 | UI, QA |
| `dish_picked` | `stove_id`, `order_id`, `dish_id` | 3 — interact bếp ready, tay trống | Lát 4 · HoangQuan23112004 | UI, QA |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | 3 — interact bàn đúng order_id | Lát 4 · HoangQuan23112004 | UI, QA |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) | 4 — ăn xong / hết ca | Lát 4 · HoangQuan23112004 | UI, QA |
| `customer_left` (`reason:"closing"`) | như trên, uy tín **không** đổi | 4 — hết ca, khách còn chờ | Lát 4 · HoangQuan23112004 | UI, QA |
| `quan_end` | `reason:"time"`, `money`, `earned`, `shift_earned`, `reputation` | 4 — sau khi dọn xong | khung + Lát 4 | UI, QA |

Dòng `end` (cuối file, mọi mode): `type:"end"`, `ticks`, `sim_tick`, `mode`, `state`, `reason` (`time`/`docked`/`fainted`/`tick_limit`), `money`, `earned`, `reputation`, `score`. Điểm = `earned + 100 × floor(reputation)` — runner đã tính.

---

## 3. Giao diện sim ↔ client/ui

```
 chonoi/sim/{gather,quan}.py  ──snapshot()/events──►  chonoi/runner.py (Session)
                                                          │            │
                                         headless: JSONL ◄┘            └► chonoi/live.py ──HTTP──► chonoi/web/index.html
                                                                              ▲  GET /state      (Lâm: HUD)
                                                                              └─ POST /input, /restart
```

- **UI chỉ đọc, không tính luật.** Mọi số trên HUD lấy từ snapshot/event. Trường chưa có thì bỏ qua, không đoán.
- **UI gửi vào** (`POST /input`): `{"move":[a,b], "interact":bool, "catch":bool}` — trạng thái phím đang giữ; cạnh lên do `chonoi/inputs.py` tính. Phím: WASD/mũi tên → `move`, E → `interact`, Space → `catch`, R → `POST /restart`.
- **UI đọc** (`GET /state`): snapshot (cùng trường với dòng snapshot headless) + `meta` (tuning của mode, ví dụ `patience_s`, `bounds`) + `events` gần nhất (tối đa 40) + `finished`, `reason`, `error`.
- **Sáng tạo của nhóm** (âm thanh, hiệu ứng, thoại) chỉ ở `chonoi/web/` hoặc lớp hiển thị; **không** thêm trường/event vào sim nếu không tắt được ở headless.

**Trường HUD tối thiểu (DoD) → đọc từ đâu:**

| Buổi | HUD | Trường snapshot |
|---|---|---|
| gather | Thời gian | `time_left_ticks` (÷ 60 → giây) |
| gather | Oxy | `player.oxygen_ticks` / `player.oxygen_max_ticks` |
| gather | Máu | `player.hp` / `player.hp_max` |
| gather | Giỏ | `hold` (thứ tự nhặt), `hold_count` / `hold_capacity` |
| gather | (thêm) | `player.at_surface`, `nodes[].ready`, `fish[]`, event `hold_full`, `choke` |
| quan | Thời gian | `time_left_ticks` |
| quan | Kho khả dụng | `stock` − tổng `customers[].reserved` (UI tự trừ để hiển thị; luật dùng hàm `_available()` ở §4) |
| quan | Món gọi + kiên nhẫn | `customers[].dish_id`, `patience_ticks_left` / (`patience_s` × 60), `order_status`, `state` |
| quan | Trạng thái bếp | `stoves[].state`, `dish`, `cook_ticks_left` |
| quan | Món trên tay | `hand` (payload hoặc `null`) |
| quan | Tiền, uy tín | `money`, `earned`, `reputation`, `score` |

---

## 4. Hợp đồng nội bộ quán (lát 3 ↔ lát 4)

Hai lát cùng sửa `QuanSim` → chốt **cấu trúc dữ liệu** và **ai ghi trường nào** trước khi code.

### 4.1. Cấu trúc (giống hệt snapshot mục D)

```python
self.stock      # v1.2: mảng cá thể {id, kind, fresh: Fraction}, tồn VẬT LÝ gồm cả phần giữ (hao 0.25/s)
self.hand       # None hoặc payload {"order_id", "dish_id", "base_price"}
self.stoves     # [{"id","pos","state": "idle|cooking|ready", "dish": payload|None, "cook_ticks_left", "ready_ticks"}]
self.customers  # chỉ khách CÒN NGỒI, mỗi khách:
{
  "id": "C1",                 # = order_id
  "table_id": "T1",
  "dish_id": "goi_bong_sung",
  "order_tick": 120,          # phase_tick lúc gọi
  "state": "waiting",         # waiting | eating
  "patience_ticks_left": 3600,
  "eat_ticks_left": 0,
  "order_status": "reserved", # reserved | assigned | unfulfillable | served
  "reserved": ["I3", "I7"],     # v1.2: mảng id cá thể (tươi nhất, hòa id); rỗng [] khi assigned/served/unfulfillable
  "base_price": None,         # chốt khi cook_started (int)
  "tip": None,                # chốt khi served (int)
}
```

Id khách mới cấp bằng `self.ids` (`IdAllocator`, họ `C`); sắp bằng `sort_by_id`. Ngẫu nhiên chọn món chỉ qua `self.rng` (`Streams`), duyệt món theo mã Unicode.

### 4.2. Ai ghi trường nào

| Chuyển trạng thái | Người ghi | Thay đổi |
|---|---|---|
| Khách đến | Lát 3 | thêm khách: `waiting`, `reserved`, `reserved = recipe`, kiên nhẫn đầy, `order_tick = phase_tick` |
| Kiên nhẫn −1 mỗi bước | Lát 3 | `patience_ticks_left` (chỉ khách `waiting`, kẹp 0) |
| Bắt đầu nấu | Lát 4 | v1.2: tiêu đúng các id trong `reserved`; `reserved = []`; `order_status = "assigned"`; `base_price = floor(menu.price × fresh TB / 100)`; bếp `cooking` + `dish = payload` |
| Nấu xong / bưng | Lát 4 | bếp `ready` → `hand = payload`, bếp `idle` |
| Phục vụ | Lát 4 | `state = "eating"`, `order_status = "served"`, `eat_ticks_left = eat_s × 60`, `tip`; `hand = None` |
| Ăn xong / hết ca | Lát 4 | `paid` → `money += amount`, `earned`, `shift_earned`, uy tín (+tip_reputation nếu tip > 0, kẹp) → gọi `_remove_customer` |
| Hết kiên nhẫn | Lát 3 | uy tín += `left_reputation_delta` (kẹp) → `customer_left(patience)` → gọi `_remove_customer` |

### 4.3. Hàm dùng chung (Lát 3 viết, Lát 4 gọi)

```python
def _available(self) -> dict:            # v1.2: số cá thể theo loại chưa giữ VÀ chưa ươn (fresh >= 30)
def _remove_customer(self, c) -> None:   # nhả c["reserved"] (không trừ stock), bỏ món của đơn c
                                         # trên bếp (bếp về idle) hoặc trên tay (hand = None), xóa khách
```

### 4.4. Thứ tự trong `QuanSim.step` (mục F, Quán) — ai sửa đoạn nào

| Bước | Nội dung | Lát |
|---|---|---|
| 1 | Giảm timer ca; kiên nhẫn (lát 3); nấu, ăn, `ready_ticks` của món đã ready đầu bước (lát 4) | 3 + 4 |
| 2 | Bếp theo id: nấu xong → `ready`, `dish_ready` | 4 |
| 3 | Di chuyển (khung) → tối đa một interact theo (khoảng cách, bếp trước bàn, id) | 4 |
| 4 | Theo id bàn: ăn xong → `paid`; kiên nhẫn 0 → `customer_left(patience)` (lát 3); hết ca → closing + `quan_end` (lát 4) | 3 + 4 |
| 5 | Ca còn giờ: lịch khách theo `phase_tick` (`first_customer_tick`, rồi mỗi `customer_interval_s × 60`), `no_dish` | 3 |

Kiểm scenario quán (mục D → mã 2) ở `chonoi/scenario.py::_validate_quan`: Lát 3 (22520160). Lát 4 báo Lát 3 các ca về bếp/tay (bếp cooking phải có timer dương và món khớp đơn; bếp và tay không giữ cùng đơn).
