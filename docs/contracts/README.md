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
- `player.pos [x,z]`, `stock` (bỏ mục 0, sắp id), `hand` (null hoặc id món đang bưng)
- `stoves[]`: `id, pos, state, dish, cook_ticks_left, ready_ticks`
- `tables[]`: `id, pos, customer_id`
- `customers[]` (sắp id): tối thiểu `id, table_id, reserved` + trường vòng đời — **[giả định]** `state` ∈ `waiting|assigned|eating`, `dish`, `patience_ticks`, `eat_ticks_left`, `price`, `tip` (chờ PRD-0 mục E, xem clarify #6).

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
| `oxygen_empty` | `{}` **[giả định]** | oxy từ dương xuống 0 |
| `choke` | `{hp}` **[giả định]** | đủ `choke_interval_ticks` tick ở oxy 0 dưới nước → −1 Máu |
| `faint` | `{}` **[giả định]** | Máu về 0; ngay sau đó `gather_end{reason:"fainted"}` với kho rỗng, dừng bước |
| `gather` | `{node_id, kind}` **[giả định]** | hái được (ở mặt nước, nút `ready` gần nhất trong `interact_radius`, hòa thì id nhỏ) |
| `fish_caught` | `{fish_id, kind, count}` **[giả định]** | `catch` dưới nước, hết hồi chiêu, có đàn trong `catch_radius`; nhận `fish_yield[kind]` con |
| `hold_full` | `{source}` **[giả định]** (`node`/`fish`) | giỏ không còn chỗ khi hái/bắt |
| `gather_end` | `{reason, inventory:{items}}` | `docked` / `time` / `fainted` — **chốt** (smoke test kiểm) |

### 3.2 quan — phát bởi `sim/quan.py`
Tên sự kiện **chốt** theo khung; `data` là **[giả định]**, chờ PRD-0 mục E (clarify #6).

| Sự kiện | `data` đề xuất | Khi nào |
|---|---|---|
| `customer_arrived` **[giả định tên]** | `{customer_id, table_id, dish}` | khách tới theo lịch `first_customer_tick` + `customer_interval_s`, có bàn trống và món nấu được → giữ chỗ nguyên liệu |
| `no_dish` | `{table_id}` | tới lượt khách nhưng không món nào đủ nguyên liệu |
| `customer_left` | `{customer_id, reputation}` | hết kiên nhẫn → `left_reputation_delta`, trả lại nguyên liệu đã giữ |
| `cook_started` | `{stove_id, dish}` | `interact` tại bếp rảnh |
| `dish_ready` | `{stove_id, dish}` | nấu đủ `cook_s` |
| `dish_picked` | `{stove_id, dish}` | `interact` tại bếp `ready`, tay trống (`carry_limit` = 1) |
| `served` | `{customer_id, dish}` | `interact` tại bàn có khách đúng món |
| `paid` | `{customer_id, price, tip, reputation}` | ăn xong `eat_s`; boa `tip_rate` nếu kiên nhẫn còn ≥ `tip_min_patience_ratio` (+`tip_reputation`) |
| `quan_end` | `{reason, money, earned, shift_earned, reputation}` | hết giờ — **chốt** (khung đã phát) |

Một bước quan tối đa **một** `interact`; chọn đối tượng theo (khoảng cách, bếp trước bàn, id nhỏ).

## Nhật ký đổi hợp đồng
| Ngày | Đổi gì | Lý do | Ai |
|---|---|---|---|
| 2026-11-21 | Chốt v1.0 phase 1 | Kickoff | Integrator |
