# Hợp đồng tích hợp — contract v1.0 (Phase 1)

> **Người giữ:** Integrator. **Trạng thái:** CHỐT cho phase 1 (2026-11-21).
> Nguồn: khung `chonoi/` + `tests/test_smoke_p1.py` (mã hóa Test Contract) + `game.contract.json`.
> Mục ghi **[giả định]** là chỗ PRD-0 chưa nói rõ / chưa đối chiếu được; câu hỏi tương ứng nằm ở [`docs/clarify.md`](../clarify.md). PO trả lời xong thì Integrator cập nhật và bỏ nhãn.
> Đổi hợp đồng: báo cả nhóm trước, ghi lý do (ADR trong `docs/adr/` hoặc ghi chú cuối file), commit riêng.

## 0. Quy tắc chung (áp cho mọi module)
- Số liệu chỉ đọc từ `game.contract.json` → `tuning.*`; không hard-code trong luật.
- 60 tick/s. Ngẫu nhiên chỉ qua `Streams` (`chonoi/rng.py`); không đồng hồ hệ thống. Cùng seed + cùng input → JSONL giống từng byte.
- Danh sách thực thể luôn sắp bằng `ids.sort_by_id`; id mới cấp bằng `IdAllocator`.
- Số thực trong JSONL làm tròn 3 chữ số (do `chonoi/jsonl.py` lo).
- Mã thoát headless: `0` bình thường · `2` tham số/đầu vào sai (kiểm **trước** khi ghi bất kỳ đầu ra nào) · `1` lỗi chạy/ghi.

## 1. Schema file kho (PRD-0 mục G)

```json
{"items": {"<id nguyên liệu>": <số nguyên >= 1>}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items`. Khóa khác → mã 2. |
| Id hợp lệ (v1.0) | `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Id lạ → mã 2. |
| Giá trị | Số nguyên ≥ 0 (không bool). Âm / không nguyên → mã 2. Khi **đọc**, mục bằng 0 được chấp nhận rồi bỏ đi. |
| Ghi | Bỏ mục bằng 0, sắp khóa theo id, JSON gọn (`,` `:`), UTF-8, có `\n` cuối; ghi qua file tạm cùng thư mục rồi `os.replace` (nguyên tử). |
| Khi nào ghi | **Đúng một lần**, khi có sự kiện `gather_end` (`docked` / `time` / `fainted`). Chạy hết `--ticks` mà chưa `gather_end` → **không đụng** file đích. |
| `fainted` | Giỏ mất hết → ghi `{"items":{}}`. |
| Nối buổi | `gather --inventory-out kho.json` → `quan --inventory kho.json`. `--inventory` và `scenario.quan.stock` không dùng cùng lúc (mã 2). |

Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json). Code: `chonoi/inventory.py`.

## 2. Giao diện `sim/*` ↔ `client/ui`

UI (cửa sổ `chonoi.live` hoặc client của nhóm) **chỉ đọc snapshot** và **chỉ gửi input**; không gọi hàm luật, không sửa trạng thái sim. Cả headless và live dùng chung `runner.Session`.

### 2.1 Lệnh UI gửi vào (Contract C, v1.0)
| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `move` | `[a, b]`, mỗi số ∈ [-1, 1] | gather: `[x, d]` (d dương = lặn xuống); quan: `[x, z]`. Độ dài > 1 thì chuẩn hóa. Giữ nguyên tới khi đổi. |
| `interact` | bool | Kích hoạt theo **cạnh lên** (false→true). Phím E. |
| `catch` | bool | Cạnh lên. Phím Space. Chỉ có nghĩa ở gather. |

File inputs headless: `{"frames":[{"tick":k, ...}]}`, `tick` tăng ngặt, trường vắng = giữ giá trị cũ; bước k đọc frame có `tick == k`. Trường lạ → mã 2.

### 2.2 Snapshot UI được đọc
Chung mọi mode (`runner._common`): `type, tick, sim_tick, mode, phase, phase_tick, state (playing|finished), time_left_ticks, money, earned, reputation, score`
với `score = earned + reputation_multiplier * floor(reputation)`.

**gather** (`GatherSim.snapshot`):
- `player`: `pos [x,d], vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface`
- `hold` (mảng id theo thứ tự nhặt, cuối = mới nhất), `hold_count`, `hold_capacity`
- `nodes[]`: `id, pos, kind, ready, regrow_ticks` · `fish[]`: `id, pos, kind, heading_deg`

**quan** (`QuanSim.snapshot`):
- `player.pos [x,z]`, `stock` (bỏ mục 0, sắp id), `hand` (payload {order_id, dish_id, base_price} hoặc null)
- `stoves[]`: `id, pos, state (idle|cooking|ready), dish, cook_ticks_left, ready_ticks`
- `tables[]`: `id, pos, customer_id (null nếu trống)`
- `customers[]` (sắp id): `id, table_id, dish_id, order_tick, state (waiting|eating), patience_ticks_left, eat_ticks_left, order_status (reserved|assigned|unfulfillable|served), reserved, base_price, tip`

Thêm trường mới vào snapshot: được (UI bỏ qua trường lạ), nhưng **không đổi tên / bỏ** trường đã liệt kê ở trên.

## 3. Danh sách sự kiện

Dòng event: `{"type":"event","tick":k+1,"phase":..,"name":..,"data":{..}}`. Trong một tick, sự kiện ghi **theo thứ tự xử lý** của bước, trước snapshot của tick đó. Người phát = module sim; người nghe = UI (hiệu ứng/HUD), QA (test), và runner (chỉ `gather_end` để ghi kho).

### 3.1 gather — phát bởi `sim/gather.py`
Thứ tự một bước: (1) đồng hồ, bộ đếm, nút mọc lại → (2) bơi + chặn mép → (3) dive/surface, oxy, ngạt, ngất → (4) `interact`: **bến trước**, rồi hái → (5) `catch` → (6) hết giờ.

| Sự kiện | `data` | Khi nào |
|---|---|---|
| `node_regrown` | `{node_id}` | `regrow_ticks` của nút về 0 |
| `dive` | `{pos}` | d đầu bước ≤ `surface_depth` và d cuối bước > `surface_depth` |
| `surface` | `{pos}` | ngược lại |
| `oxygen_empty` | `{oxygen_ticks: 0}` | oxy từ dương chạm 0 |
| `choke` | `{hp}` | đủ `choke_interval_ticks` (60) tick ở oxy 0 dưới nước → −1 Máu |
| `faint` | `{cause: "choke", lost: [...], hp: 0}` | Máu về 0; rớt giỏ theo LIFO; ngay sau đó `gather_end{reason:"fainted"}` với kho rỗng, dừng bước |
| `gather` | `{node_id, kind, amount: 1}` | hái được (ở mặt nước, nút `ready` gần nhất trong `interact_radius`, hòa thì id nhỏ) |
| `fish_caught` | `{fish_id, kind, yield}` | `catch` dưới nước, hết hồi chiêu, có đàn trong `catch_radius`; nhận `fish_yield[kind]` con |
| `hold_full` | `{action: "gather"|"catch", node_id|fish_id, required, free}` | giỏ không còn đủ chỗ khi hái/bắt |
| `gather_end` | `{reason: "docked"|"time"|"fainted", inventory: {items: {...}}}` | kết thúc buổi sáng (cập bến / hết giờ / ngất) |

### 3.2 quan — phát bởi `sim/quan.py`
Thứ tự một bước: (1) đồng hồ, timer ca, nấu, ăn, kiên nhẫn → (2) món nấu xong thành ready → (3) di chuyển + tối đa 1 `interact` (bếp trước bàn) → (4) ăn xong trả tiền, kiên nhẫn 0 rời bàn, hết ca đóng quán → (5) khách mới theo lịch.

| Sự kiện | `data` | Khi nào |
|---|---|---|
| `customer_arrived` | `{order_id, table_id, dish_id}` | khách tới theo lịch `first_customer_tick` + `customer_interval_s`, có bàn trống và món nấu được → giữ chỗ nguyên liệu |
| `no_dish` | `{}` | tới lượt khách, có bàn trống nhưng không món nào đủ nguyên liệu khả dụng |
| `customer_left` | `{order_id, table_id, reason: "patience"|"closing", reputation}` | hết kiên nhẫn (trừ `left_reputation_delta`) hoặc đóng ca (không trừ) |
| `cook_started` | `{stove_id, order_id, dish_id, items, base_price}` | `interact` tại bếp idle; tiêu đúng nguyên liệu giữ của đơn cũ nhất |
| `dish_ready` | `{stove_id, order_id, dish_id}` | nấu đủ `cook_s` tick |
| `dish_picked` | `{stove_id, order_id, dish_id}` | `interact` tại bếp `ready`, tay trống |
| `served` | `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}` | `interact` tại bàn mang đúng món |
| `paid` | `{order_id, table_id, base_price, tip, amount, reason: "finished_eating"|"closing"}` | ăn xong `eat_s` hoặc bị đóng ca |
| `quan_end` | `{reason: "time", money, earned, shift_earned, reputation}` | hết giờ ca |

Một bước quan tối đa **một** `interact`; chọn đối tượng theo (khoảng cách, bếp trước bàn, id nhỏ).

## Nhật ký đổi hợp đồng
| Ngày | Đổi gì | Lý do | Ai |
|---|---|---|---|
| 2026-11-21 | Chốt v1.0 phase 1 | Kickoff | Integrator |
| 2026-11-21 | Cập nhật đầy đủ payload sự kiện và snapshot theo PRD-0 Phase 1 | Đối chiếu PRD-0 mục E, F | Integrator (ToanLee5433) |
