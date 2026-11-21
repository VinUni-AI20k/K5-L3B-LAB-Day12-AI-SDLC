# Hợp đồng tích hợp (Phase 1, Test Contract v1.0)

Người giữ: Integrator. Chốt trong kickoff. Muốn đổi tên sự kiện, trường `data`, schema kho hay cấu trúc khách thì báo cả nhóm trước, rồi ghi ADR trong `docs/adr/`, vì thay đổi ảnh hưởng nhiều lát và test ẩn.

## 1. File kho (PRD-0 mục G)

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Gốc chỉ có khóa `items`. Giá trị là object `kind -> số nguyên không âm`.
- `kind` chỉ thuộc `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Kind vắng tính là 0, bên ghi bỏ khóa có lượng 0. Kho rỗng là `{"items":{}}`.
- Bên đọc (`quan --inventory`) từ chối sai schema, kind lạ, số âm hoặc không nguyên bằng mã thoát 2.
- `gather --inventory-out` ghi đúng một lần khi có `gather_end`, nội dung khớp `inventory` trong event đó. Ngất ghi kho rỗng. Chạm `--ticks` trước khi kết thúc buổi thì không tạo và không ghi đè file.
- Ghi qua file tạm cùng thư mục rồi thay thế nguyên tử (`chonoi/inventory.py`).
- Trần giỏ không áp lên kho quán.
- File mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json).

Smoke hai tiến trình:

```bash
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Snapshot quán ở tick 0 phải có `"stock":{"bong_sung":2,"ca_loc":1}`.

## 2. Danh sách sự kiện (PRD-0 mục E)

Event là dòng `{"type":"event","tick":k+1,"phase":...,"name":...,"data":{...}}`, ghi theo thứ tự xử lý trong bước, trước snapshot của tick đó. `items` và `lost` là mảng kind.

### Gather

| Sự kiện | `data` | Ai phát (hàm) |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển, chỉ khi đổi phía biên mặt nước (`d <= surface_depth` là mặt nước) | A, `_dive_surface` |
| `oxygen_empty` | `oxygen_ticks: 0`, khi oxy từ dương xuống 0 | A, `_oxygen_and_choke` |
| `choke` | `hp` sau khi trừ | A, `_oxygen_and_choke` |
| `faint` | `cause: "choke"`, `lost` (giỏ theo thứ tự bỏ, nhặt sau bỏ trước), `hp: 0` | A, `_oxygen_and_choke` |
| `gather` | `node_id`, `kind`, `amount` | B, `_try_harvest` |
| `node_regrown` | `node_id` | khung (`step`, bước 1) |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | B |
| `fish_caught` | `fish_id`, `kind`, `yield` | B, `_try_catch` |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` theo mục 1 | khung (`_finish`) |

Thứ tự trong một bước gather: `node_regrown` → `dive`/`surface` → `oxygen_empty` → `choke` → `faint` + `gather_end(fainted)` (dừng) → `gather_end(docked)` hoặc `gather`/`hold_full` → `fish_caught`/`hold_full` → `gather_end(time)`.

### Quán

| Sự kiện | `data` | Ai phát |
|---|---|---|
| `customer_arrived` | `order_id`, `table_id`, `dish_id` | C, `_spawn_customer` |
| `no_dish` | `{}` khi có bàn trống mà không món nào đủ kho khả dụng | C, `_spawn_customer` |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`/`closing`), `reputation` | C, `_settle_customers` |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (sắp theo kind), `base_price` | D, `_interact` |
| `dish_ready` | `stove_id`, `order_id`, `dish_id` | D, `_stoves_ready` |
| `dish_picked` | `stove_id`, `order_id`, `dish_id` | D, `_interact` |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` | D, `_interact` |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) | D, `_pay_customers` |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation` | khung (`step`) |

Thứ tự gọi trong `QuanSim.step` (đổi thì báo nhóm): `_tick_timers` → `_stoves_ready` → `_move` → `_interact(inp, events)` (D tự kiểm cạnh lên `interact`) → `_settle_customers(events)` (gọi `_pay_customers` của D trước, rồi xử lý khách chờ bỏ đi hoặc `closing`) → `_spawn_customer` (tự bỏ qua khi hết giờ) → `quan_end` nếu hết ca.

## 3. Dữ liệu khách dùng chung giữa lát 3 (C) và lát 4 (D)

Mỗi khách trong `QuanSim.customers` là một dict theo PRD-0 mục D:

| Trường | Kiểu | Ghi chú | Ai ghi |
|---|---|---|---|
| `id` | chuỗi | Cũng là `order_id`. Cấp bằng `self.ids.new("C")` | C |
| `table_id` | chuỗi | Bàn trống id nhỏ nhất | C |
| `dish_id` | chuỗi | Một trong 3 món | C |
| `order_tick` | số nguyên | `phase_tick` lúc khách đến | C |
| `state` | `waiting` / `eating` | | C tạo, D đổi sang `eating` |
| `patience_ticks_left` | số nguyên | Đầy = `patience_s * 60`, giảm từ bước sau khi đến | C |
| `eat_ticks_left` | số nguyên | `eat_s * 60` khi được phục vụ | D |
| `order_status` | `reserved` / `assigned` / `unfulfillable` / `served` | | C tạo `reserved`, D đổi |
| `reserved` | object kind → số | Đúng công thức món; rỗng sau khi bếp lấy | C tạo, D xóa khi nấu |
| `base_price` | số nguyên | Chốt khi `cook_started` | D |
| `tip` | số nguyên | `floor(base_price * tip_rate)` nếu tỷ lệ kiên nhẫn còn lại ≥ `tip_min_patience_ratio`, ngược lại 0 | D |

Món trên bếp hoặc trên tay là payload `{order_id, dish_id, base_price}`. Kho khả dụng = `stock` trừ tổng `reserved` của các khách (`QuanSim.available_stock()`). Khi khách rời (`_customer_leaves`): bỏ khách khỏi danh sách là nhả `reserved`, rồi gọi `self._drop_order(order_id)` để D bỏ món của đơn trên bếp hoặc trên tay. Nguyên liệu đã nấu không hoàn lại.

## 4. Giao diện mô phỏng với UI

- Headless và cửa sổ chơi dùng chung lớp sim qua `runner.Session`. UI không chứa luật.
- UI chỉ đọc snapshot qua `GET /state` (cùng trường với dòng snapshot của headless, thêm `meta` và `events` gần nhất).
- UI chỉ gửi phím qua `POST /input` `{"move":[a,b],"interact":bool,"catch":bool}` và `POST /restart`.
- Snapshot headless chỉ chứa trường theo PRD-0 mục E. Trường phục vụ riêng cho hiển thị thì tính ở client, ví dụ kho khả dụng.
