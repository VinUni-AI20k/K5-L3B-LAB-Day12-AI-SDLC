# Hợp đồng tích hợp — Phase 1 (Test Contract v1.0)

> Chốt ở kickoff P1. Đổi hợp đồng: báo cả nhóm, PR cần người khác duyệt, ghi lý do (ADR hoặc mục "Lịch sử thay đổi" cuối file).
> Nguồn: PRD-0 mục C (inputs), E (output/sự kiện), F (luật), G (kho). Số liệu chỉ đọc từ `game.contract.json`.

## 1. File kho (gather → quan) — PRD-0 mục G

**Schema**

```json
{"items": {"<kind>": <int ≥ 0>, ...}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | chỉ có `items` (object). Thêm khóa khác → bên đọc từ chối (mã 2) |
| `kind` hợp lệ | `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung` (`chonoi/inventory.py: KINDS_P1`). Kind lạ → mã 2 |
| Giá trị | số nguyên không âm. Âm / số thực / bool / chuỗi → mã 2 |
| Kind vắng | tính là 0. **Bên ghi bỏ khóa có lượng 0** |
| Kho rỗng | `{"items":{}}` |
| Trần giỏ | `hold_capacity` **không** áp lên kho quán |

**Ví dụ hợp lệ** (đúng kho của smoke test dock: giỏ `["ca_loc","bong_sung","bong_sung"]`)

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

**Ví dụ không hợp lệ (mã 2):** `{"items":{"ca_loc":-1}}` · `{"items":{"ca_tra":1}}` · `{"items":{"ca_loc":1.5}}` · `{"ca_loc":1}` · `{"items":{},"money":0}`

**Ai ghi / ai đọc / khi nào**

| | Gather (ghi, `--inventory-out`) | Quán (đọc, `--inventory`) |
|---|---|---|
| Khi nào | đúng **một lần** khi có `gather_end` (`time` / `docked` / `fainted`) | lúc khởi tạo, trước khi ghi JSONL |
| Nội dung | khớp object `inventory` trong event `gather_end`; ngất → `{"items":{}}` | thành `stock` (gồm cả phần sẽ giữ chỗ) |
| Chạm `--ticks` trước khi kết thúc | **không** tạo và không ghi đè file | — |
| Cách ghi | file tạm cùng thư mục → thay thế nguyên tử (`inventory.write_inventory`) | — |
| Thiếu file | — | thiếu cả `--inventory` lẫn `scenario.quan.stock` → kho rỗng; khai **cả hai** → mã 2 |

Đầu lượt quán độc lập: `money = earned = 0`, uy tín theo `reputation_initial` (trừ khi scenario khai).

## 2. Giao diện `sim/*` ↔ `client/ui`

UI (P1: `chonoi.live`) **chỉ đọc snapshot** và **chỉ gửi lệnh qua `InputState`**, không gọi thẳng vào luật. Mọi thứ hiển thị phải suy ra được từ snapshot.

**Lệnh UI gửi vào** (cùng format frame của `--inputs`, mục C)

| Trường | Kiểu | Phím gợi ý | Ý nghĩa |
|---|---|---|---|
| `move` | `[a, b]`, mỗi số ∈ [−1, 1], chuẩn hóa nếu dài > 1 | WASD / mũi tên | gather: `b > 0` = lặn xuống · quan: `b > 0` = về bắc |
| `interact` | bool, tác động ở **cạnh lên** | E | gather: cập bến / hái · quan: nấu / bưng / phục vụ |
| `catch` | bool, cạnh lên | Space | gather: bắt cá (quan: bỏ qua) |

**Trạng thái UI được đọc** (snapshot, mục E)

| Mode | Trường | HUD tối thiểu dùng |
|---|---|---|
| chung | `tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score` | thời gian, tiền, uy tín |
| gather | `player{pos, vel, heading_deg, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks, oxygen_max_ticks, hp_max, at_surface}`, `hold, hold_count, hold_capacity, nodes[]{…, ready}, fish[]` | oxy, Máu, giỏ |
| quan | `player{pos, vel}, stock, hand, stoves[]{id, pos, state, dish, cook_ticks_left, ready_ticks}, tables[]{id, pos, customer_id}, customers[]{…}` (chỉ khách còn ngồi) | kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay |

Điểm: `score = earned + reputation_multiplier × floor(reputation)`.

## 3. Danh sách sự kiện — mục E

Event được phát tại tick `k+1` của bước `k`, theo thứ tự xử lý, trước snapshot. Hiện người "nghe" chỉ có JSONL, test và UI (hiện thông báo); không module nào phụ thuộc event của module khác, chỉ phụ thuộc file kho.

**Gather** — phát bởi `chonoi/sim/gather.py` (Phong)

| name | data | Khi nào |
|---|---|---|
| `dive` / `surface` | `pos` (sau di chuyển) | đổi phía biên mặt nước (`d > 0.5` ↔ `d ≤ 0.5`) |
| `oxygen_empty` | `oxygen_ticks: 0` | oxy vừa từ dương xuống 0 |
| `choke` | `hp` (sau trừ) | `zero_oxy_ticks` đủ 60 |
| `faint` | `cause: "choke", lost, hp: 0` | Máu về 0; `lost` theo LIFO (nhặt sau bỏ trước) |
| `gather` | `node_id, kind, amount` | hái thành công |
| `node_regrown` | `node_id` | `regrow_ticks` 1 → 0 |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required, free` | thiếu chỗ trong giỏ |
| `fish_caught` | `fish_id, kind, yield` | bắt được đàn |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` (= object mục 1) | kết thúc buổi sáng |

**Quán** — phát bởi `chonoi/sim/quan.py` (Khánh)

| name | data | Khi nào |
|---|---|---|
| `customer_arrived` | `order_id, table_id, dish_id` | khách mới ngồi + giữ chỗ |
| `no_dish` | `{}` | có bàn trống nhưng không món nào đủ nguyên liệu khả dụng |
| `cook_started` | `stove_id, order_id, dish_id, items` (sắp theo kind), `base_price` | bếp idle nhận đơn reserved cũ nhất |
| `dish_ready` | `stove_id, order_id, dish_id` | nấu xong |
| `dish_picked` | `stove_id, order_id, dish_id` | bưng món lên tay trống |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | giao đúng bàn |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (`finished_eating`/`closing`) | khách trả tiền |
| `customer_left` | `order_id, table_id, reason` (`patience`/`closing`), `reputation` | khách rời không ăn |
| `quan_end` | `reason: "time", money, earned, shift_earned, reputation` | hết ca, đã dọn xong |

Dòng cuối JSONL luôn là `{"type":"end", ticks, sim_tick, mode, state, reason, money, earned, reputation, score}` do `chonoi/runner.py` ghi (`reason` thêm `tick_limit` khi gameplay chưa xong).

## 4. Smoke tích hợp (phải xanh trước khi tag)

```bash
# dock.json: {"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
# dock-inputs.json: {"frames":[{"tick":0,"interact":true}]}
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
# kỳ vọng: snapshot quán tick 0 có "stock":{"bong_sung":2,"ca_loc":1}
```

Đã có sẵn trong `tests/test_smoke_p1.py`.

## Lịch sử thay đổi

| Ngày | Đổi gì | Lý do | Ai duyệt |
|---|---|---|---|
| 2026-11-21 | Bản đầu (P1) | kickoff | Khuê (Integrator) |
