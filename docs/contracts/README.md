# Hợp đồng tích hợp — Phase 1 (Test Contract v1.0)

> Chốt lúc kickoff Phase 1. Người giữ: Integrator (nglngnguyen-gh). Đổi hợp đồng phải báo cả nhóm và ghi lý do trong `docs/adr/`.
> Nguồn: PRD-0 mục D, E, G. Phần cài đặt: `chonoi/inventory.py`, `chonoi/runner.py`, `chonoi/live.py`.

## 1. File kho (Lặn & Hái → Mở Quán)

### Schema

```json
{"items": {"<kind>": <int ≥ 0>, ...}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items`. Khóa gốc khác → mã 2. |
| `kind` | Chỉ `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Kind lạ → mã 2. |
| Số lượng | Số nguyên không âm (không nhận `bool`, số thực, số âm → mã 2). Kind vắng tính là 0. |
| Bên ghi | Bỏ khóa có lượng 0, sắp khóa theo mã Unicode, JSON gọn (`,` `:`), một dòng, kết thúc `\n`, UTF-8. Kho rỗng là `{"items":{}}`. |
| Trần | Trần giỏ (`hold_capacity`) không áp lên kho quán. |

### Ai ghi, khi nào (lát 2 — `gather`)

- Chỉ `gather --inventory-out <file>` ghi, và ghi **đúng một lần** khi có `gather_end`.
- Nội dung file **giống hệt** `gather_end.data.inventory`.
- `reason`:
  - `docked` / `time`: kho là phần còn trong giỏ.
  - `fainted`: kho rỗng `{"items":{}}`.
- Chạm `--ticks` trước khi buổi sáng kết thúc: **không tạo, không ghi đè** file.
- Ghi file tạm cùng thư mục rồi thay thế nguyên tử (`write_inventory`).

### Ai đọc (lát 3, 4 — `quan`)

- `quan --inventory <file>` nạp thành `stock` (gồm cả phần giữ chỗ).
- Khai cả `--inventory` và `scenario.quan.stock` → mã 2.
- Thiếu cả hai → kho rỗng. Tiền và `earned` đầu lượt bằng 0.
- Kho khả dụng để chọn món = tồn vật lý − tổng `reserved` của các đơn.

### Ví dụ hợp lệ

- [`inventory.sample.json`](inventory.sample.json): `{"items":{"bong_sung":2,"ca_loc":1}}`
- Kho rỗng: `{"items":{}}`

Ví dụ **không hợp lệ** (mã 2): `{"items":{"ca_loc":-1}}`, `{"items":{"ca_tra":1}}`, `{"items":{"ca_loc":1.5}}`, `{"items":{}, "money":0}`.

### Smoke hai tiến trình (AC-P1-50)

```bash
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json \
  --ticks 600 --out g.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory kho.json --ticks 0 --out q.jsonl
```

Kỳ vọng: `kho.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`, snapshot quán ở tick 0 có `"stock":{"bong_sung":2,"ca_loc":1}`.

## 2. Giao diện `sim/*` ↔ runner ↔ `client/ui`

```
sim = GatherSim | QuanSim(tuning, scenario, streams, ids[, inventory])
events = sim.step(inp)   # một tick; trả list (name, data)
sim.snapshot()           # trường riêng của mode (mục 4)
sim.done, sim.reason, sim.time_left_ticks, sim.money, sim.earned, sim.reputation
```

- **Runner** lo `tick`, `sim_tick`, `phase_tick`, thứ tự ghi event → snapshot, dòng `end`, điểm.
- **UI (`chonoi.live`)** chỉ **đọc**: `GET /state` trả snapshot + `meta` + `events`. UI **gửi vào** duy nhất `POST /input` `{"move":[a,b],"interact":bool,"catch":bool}`. UI không sửa trạng thái sim.
- Đồ họa, âm thanh, RNG giao diện nằm ngoài sim; headless không chạy UI.

## 3. Sự kiện

`data` đúng tên và thứ tự trường như dưới. Mảng `items`, `lost` là mảng `kind`.

### `gather` (lát 1, 2)

| `name` | `data` | Phát bởi |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển; chỉ khi đổi phía `d = surface_depth` | lát 1 |
| `oxygen_empty` | `oxygen_ticks: 0`, khi từ dương xuống 0 | lát 1 |
| `choke` | `hp` sau khi trừ | lát 1 |
| `faint` | `cause: "choke"`, `lost` (LIFO: nhặt sau bỏ trước), `hp: 0` | lát 1 |
| `gather` | `node_id`, `kind`, `amount` | lát 2 |
| `node_regrown` | `node_id` | lát 2 (đếm ngược đã có) |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | lát 2 |
| `fish_caught` | `fish_id`, `kind`, `yield` | lát 2 |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` (object mục 1) | lát 1 (`fainted`), lát 2 (`docked`, `time`) |

### `quan` (lát 3, 4)

| `name` | `data` | Phát bởi |
|---|---|---|
| `customer_arrived` | `order_id`, `table_id`, `dish_id` | lát 3 |
| `no_dish` | `{}` (có bàn nhưng thiếu món) | lát 3 |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`/`closing`), `reputation` | lát 3 |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (sắp theo kind), `base_price` | lát 4 |
| `dish_ready` / `dish_picked` | `stove_id`, `order_id`, `dish_id` | lát 4 |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | lát 4 |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) | lát 4 |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation` | lát 4 (khung đã có) |

## 4. Trạng thái chia sẻ giữa lát 3 và lát 4

Hai lát cùng sửa `chonoi/sim/quan.py`; thống nhất cấu trúc sau để làm song song bằng fixture.

**Khách** (lát 3 tạo, lát 4 cập nhật):

```json
{"id":"C1","table_id":"T1","dish_id":"goi_bong_sung","order_tick":120,
 "state":"waiting","patience_ticks_left":3600,"eat_ticks_left":0,
 "order_status":"reserved","reserved":{"bong_sung":2},"base_price":0,"tip":0}
```

- `state`: `waiting` → `eating`.
- `order_status`:
  - `reserved`: lát 3 đặt khi gọi món, giữ đúng công thức.
  - `assigned`: lát 4 đặt khi bắt đầu nấu, `reserved` thành `{}`, món ở bếp hoặc trên tay.
  - `served`: lát 4 đặt khi giao món.
  - `unfulfillable`: còn chờ, `reserved` rỗng, không có món.
- `id` khách cấp bằng `IdAllocator` (tiền tố `C`); `order_id` = id khách.

**Payload món** (bếp `dish`, `hand`): `{"order_id":"C1","dish_id":"goi_bong_sung","base_price":40}`.

**Bếp**: `{"id":"B1","pos":[2,8],"state":"idle|cooking|ready","dish":<payload|null>,"cook_ticks_left":int,"ready_ticks":int}`.

**Hàm dùng chung** (lát 3 viết, lát 4 gọi): `_release(customer)` nhả phần giữ, bỏ món của đơn ở bếp hoặc trên tay khi khách rời.
