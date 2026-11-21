# Hợp đồng tích hợp — Test Contract v1.1 (Phase 2)

> **Người giữ:** Integrator. **Trạng thái:** CHỐT theo TICKET-02 (Phase 2).
> Nguồn chuẩn: PRD-0 mục A–G (Test Contract v1.0). File này là bản tóm tắt cho nhóm/agent; chỗ nào lệch PRD thì PRD thắng.
> Đổi hợp đồng: báo cả nhóm trước, ghi lý do (ADR trong `docs/adr/` hoặc nhật ký cuối file), commit riêng.

## 0. Quy tắc chung (mọi module)
- 60 tick/s, độc lập cửa sổ/GPU. Đơn vị mét. gather `[x, d]` (x hướng đông, d tăng xuống, 0° = +x, 90° = xuống); quan `[x, z]` (z hướng bắc).
- Số liệu chỉ đọc từ `game.contract.json` → `tuning.*`. Thời gian `_s` quy ra tick nguyên ở 60 Hz. Tiền là số nguyên (nghìn đồng).
- Ngẫu nhiên chỉ qua `Streams`; không đồng hồ thực. Cùng bản chạy + seed + tham số + đầu vào → JSONL **và** file kho giống từng byte. Duyệt ứng viên theo thứ tự cố định, id món theo mã Unicode.
- Sắp id bằng khóa (tiền tố, hậu tố số hoặc −1, id gốc): `F2` trước `F10`. Id mới nối sau hậu tố lớn nhất của họ id đã nạp/phát (`IdAllocator`).
- Khoảng cách Euclid, **tính cả đúng mép** bán kính. So bán kính và tính giá trước khi làm tròn; tọa độ xuất 3 chữ số thập phân.
- Mã thoát headless: `0` kết thúc lượt hoặc chạm `--ticks` · `2` cờ/dữ liệu sai hoặc fixture mâu thuẫn (kiểm **trước** khi ghi JSONL/kho) · `1` lỗi thực thi/ghi. Chẩn đoán qua stderr.
- Dung sai khi chấm: tọa độ ±0.1 m, uy tín ±0.01, đo thời gian ±2 tick. Tiền, điểm, id, số lượng, countdown, lý do, tick của event biên: **chính xác**.

## 1. Schema file kho (mục G)

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items`: object kind → số nguyên ≥ 0. Kind vắng tính 0. Kho rỗng `{"items":{}}`. |
| Kind hợp lệ | `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`. Sai schema / kind lạ / giá trị ngoài miền → mã 2. |
| Ghi | Bỏ khóa có lượng 0, sắp theo kind, ghi file tạm cùng thư mục rồi thay thế nguyên tử. |
| Khi nào ghi | `gather --inventory-out` ghi **đúng một lần** khi có `gather_end`; nội dung khớp `data.inventory` của event đó. Ngất → `{"items":{}}`. Chạm `--ticks` trước khi buổi sáng kết thúc → không tạo, không ghi đè. |
| Bên đọc (quan) | `--inventory` hoặc `scenario.quan.stock`, không cả hai (mã 2). Thiếu cả hai → kho rỗng. Trần giỏ không áp lên kho quán. Tiền/`earned` đầu lượt = 0; uy tín theo tuning trừ khi scenario khai. |

Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json). Code: `chonoi/inventory.py`.

**Smoke hai tiến trình (bắt buộc chạy trên `main` trước khi tag):**
```bash
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```
Snapshot quán tick 0 phải có `"stock":{"bong_sung":2,"ca_loc":1}`.

## 2. Giao diện `sim/*` ↔ `client/ui`

UI **chỉ gửi input** và **chỉ đọc snapshot**; không gọi hàm luật, không sửa trạng thái sim. Headless và `chonoi.live` dùng chung `runner.Session`. Phần sáng tạo của nhóm phải tắt ở headless hoặc không đổi tick/event/tiền/uy tín/snapshot.

### 2.1 Lệnh UI gửi vào (mục C)
| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `move` | `[a, b]` hữu hạn, mỗi số ∈ [-1, 1] | gather `[x, d]` (b dương = xuống); quan `[x, z]` (b dương = bắc). Độ dài > 1 thì chuẩn hóa. |
| `interact` | bool, **cạnh lên** | gather: cập bến / hái. quan: nấu / bưng / phục vụ. Phím E. |
| `catch` | bool, **cạnh lên** | gather: bắt cá. Phím Space. Sai pha thì bỏ qua. |

File inputs: `{"frames":[{"tick":k,...}]}`, `tick` nguyên ≥ 0 tăng nghiêm ngặt; frame chỉ cập nhật trường có mặt; trước frame đầu `move=[0,0]`, nút `false`. Trường lạ, sai kiểu, tick lặp/giảm → mã 2.

### 2.2 Snapshot (mục E)
Chụp ở tick 0 (sau dựng fixture), ở bội số `--snapshot-every` (mặc định 10) và ở tick dừng; mỗi tick tối đa một snapshot.

**Chung:** `type:"snapshot", tick, sim_tick, mode, phase, phase_tick, state (playing|finished), time_left_ticks, money, earned, reputation, score` với `score = earned + 100 × floor(reputation)`.

**gather:**
- `player`: `pos, vel, heading_deg, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks` + `oxygen_max_ticks, hp_max, at_surface`
- `hold` (mảng kind theo thứ tự nhặt, mới nhất cuối), `hold_count`, `hold_capacity`
- `nodes[]`: `id, kind, pos, regrow_ticks, ready` (`ready` = `regrow_ticks == 0`) · `fish[]`: `id, kind, pos, heading_deg`

**quan:**
- `player {pos, vel}`, `stock` (gồm cả phần giữ chỗ), `hand` (payload món `{order_id, dish_id, base_price}` hoặc `null`)
- `stoves[]`: `id, pos, state (idle|cooking|ready), dish, cook_ticks_left, ready_ticks`
- `tables[]`: `id, pos, customer_id` (trống = `null`)
- `customers[]` (chỉ khách còn ngồi): `id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status (reserved|assigned|unfulfillable|served), reserved {kind: số}, base_price, tip`

Dòng cuối: `{"type":"end", ticks, sim_tick, mode, state, reason, money, earned, reputation, score}`; `reason` ∈ `time|docked|fainted` (gather), `time` (quan), hoặc `tick_limit`. Kết thúc đúng bước cuối được cấp thì ưu tiên lý do gameplay.

## 3. Sự kiện (mục E) — phát bởi `sim/*`, nghe bởi UI (HUD/hiệu ứng), QA (test), runner (`gather_end` → ghi kho)

Dòng event: `{"type":"event","tick":k+1,"phase":..,"name":..,"data":{..}}`, ghi theo thứ tự xử lý rồi mới tới snapshot. `items` và `lost` là **mảng kind**; `lost` theo LIFO (nhặt sau bỏ trước).

### 3.1 gather — `sim/gather.py`
Thứ tự một bước (mục F):
1. Đồng hồ, timer ca, hồi bắt, hồi nút. Nút 1 → 0 phát `node_regrown` (theo id), hái được ngay.
2. Bơi, chặn biên; so đầu/cuối bước → `dive`/`surface`.
3. Oxy theo d **cuối** bước: mặt nước (`d ≤ 0.5`) +6, kẹp max, reset đếm ngạt; dưới nước −1, kẹp 0. Mỗi bước kết thúc dưới nước với oxy 0 (kể cả bước vừa chạm 0) → `zero_oxy_ticks += 1`; đủ 60 → đặt 0, −1 Máu, `choke`. Máu 0 → bỏ giỏ LIFO, `faint`, `gather_end fainted` (kho rỗng), dừng.
4. Cạnh `interact`: bến trước (khoảng cách tới `dock_pos` ≤ `dock_radius` → `gather_end docked`). Ngoài bến, chỉ hái khi ở mặt nước: nút `ready` gần nhất trong `interact_radius`, hòa theo id.
5. Cạnh `catch`: hết hồi **và** dưới nước → đàn gần nhất trong `catch_radius`, hòa theo id. Đủ chỗ: thêm toàn bộ yield, xóa đàn, đặt hồi. Thiếu chỗ: `hold_full`, giữ đàn, **không** đặt hồi, không thử đàn khác. Không có đàn trong tầm: không event, không hồi.
6. Timer ca 0 → `gather_end time` ở mọi độ sâu, giữ giỏ sau các hành động trên.

| Sự kiện | `data` |
|---|---|
| `node_regrown` | `{node_id}` |
| `dive` / `surface` | `{pos}` (vị trí sau di chuyển) |
| `oxygen_empty` | `{oxygen_ticks: 0}` |
| `choke` | `{hp}` (sau khi trừ) |
| `faint` | `{cause: "choke", lost: [kind…] (LIFO), hp: 0}` |
| `gather` | `{node_id, kind, amount}` |
| `fish_caught` | `{fish_id, kind, yield}` — một event mỗi đàn |
| `hold_full` | `{action: "gather"\|"catch", node_id \| fish_id, required, free}` |
| `gather_end` | `{reason: "time"\|"docked"\|"fainted", inventory: {items}}` |

### 3.2 quan — `sim/quan.py`
Thứ tự một bước (mục F):
1. Đồng hồ, timer ca, nấu, ăn, kiên nhẫn. `ready_ticks` chỉ tăng cho món đã ready từ đầu bước.
2. Bếp theo id: nấu xong → `ready`, `ready_ticks = 0` (`burn_s: null`, không cháy).
3. Di chuyển, rồi tối đa **một** interact chọn theo (khoảng cách, bếp trước bàn, id); đối tượng không tương tác được → bỏ lượt.
   - Bếp `idle`: lấy đơn `reserved` cũ nhất (order_tick, rồi id bàn), tiêu đúng nguyên liệu giữ, chốt giá, nấu.
   - Bếp `ready` + tay trống: giao món, bếp về `idle`.
   - Bàn nhận đúng `order_id`: khách ăn với timer đầy; boa = `floor(base_price × tip_rate)` nếu tỷ lệ kiên nhẫn còn lại (sau bước 1) ≥ `tip_min_patience_ratio`, không thì 0.
4. Theo id bàn: ăn xong → trả tiền, rời bàn. Còn giờ: khách `waiting` kiên nhẫn 0 rời, uy tín `+ left_reputation_delta`. Hết ca: khách đang ăn trả ngay, khách chờ rời `closing` không trừ uy tín, rồi `quan_end`. Khách rời: nhả phần giữ, bỏ món của đơn (bếp/tay); nguyên liệu đã dùng không hoàn. Boa dương: `+ tip_reputation`. Uy tín kẹp `[reputation_min, reputation_max]`.
5. Còn giờ: lượt khách tại `first_customer_tick`, rồi mỗi `customer_interval_s × 60` (theo `phase_tick`). Không bàn trống → bỏ lượt. Có bàn → bàn trống id nhỏ nhất; chọn đều theo seed trong các món đủ nguyên liệu khả dụng (tồn − giữ); không món nào → `no_dish`. Khách mới giữ công thức ngay, `order_tick = phase_tick`, kiên nhẫn đầy, giảm từ bước sau.

| Sự kiện | `data` |
|---|---|
| `customer_arrived` | `{order_id, table_id, dish_id}` |
| `no_dish` | `{}` |
| `cook_started` | `{stove_id, order_id, dish_id, items: [kind…] (sắp theo kind), base_price}` |
| `dish_ready` / `dish_picked` | `{stove_id, order_id, dish_id}` |
| `served` | `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}` |
| `paid` | `{order_id, table_id, base_price, tip, amount, reason: "finished_eating"\|"closing"}` |
| `customer_left` | `{order_id, table_id, reason: "patience"\|"closing", reputation}` |
| `quan_end` | `{reason: "time", money, earned, shift_earned, reputation}` |

## Nhật ký đổi hợp đồng
| Ngày | Đổi gì | Lý do | Ai |
|---|---|---|---|
| 2026-11-21 | Chốt v1.0 bản nháp từ code khung | Kickoff, PRD chưa mở | Integrator |
| 2026-11-21 | Đối chiếu PRD-0: sửa `data` sự kiện gather/quan, trường khách trong snapshot quan, thứ tự bước; bỏ toàn bộ nhãn [giả định] | PRD-0 phát hành 08:02 | QA (czx04) |
| 2026-11-21 | Nâng cấp Test Contract v1.1 cho Phase 2: thêm N5/N6 kèo nèo, cá kèo, cá bơi phản xạ mép & đổi hướng tick 120, sinh cá tick 360, quái Cá Sấu Năm Chèo M1/M2 | TICKET-02 Phase 2 | Integrator (ToanLee5433) |


## Phase 2 — Vòng ngày / Shop / pause
Nguồn đầy đủ: [`TICKET-02`](../tickets/TICKET-02.md), mục 2 và 4. CLI thêm `--mode day --days 1..5` (mặc định 1); cờ file kho chỉ cho mode độc lập. Live day mặc định 5 Ngày.

- `DaySim` giữ Streams và IdAllocator xuyên Ngày, mang `money/earned/reputation/upgrades`; mẫu scenario `gather`/`quan` áp lại mỗi Ngày. `day` chứa trạng thái xuyên Ngày và override kế hoạch.
- Gather → quan → shop đổi pha trong cùng tick kết thúc; event giữ pha/Ngày cũ, `phase_start` và snapshot pha mới có `phase_tick:0`. `days_completed` chỉ tăng sau `shop_end`, kể cả Ngày cuối. Trước snapshot tick 0 phát `day_start`, `day_plan`, `phase_start`.
- Shop đọc `tuning.shop`: 600 bước hoạt động, xử lý `buy` trước cạnh `shop_done`, ưu tiên done ở bước cuối. Cấp mua tăng ngay, sao vào `active_upgrades` khi dựng Ngày kế. Trừ `money`, giữ `earned` và score. Kho dư bỏ đầu Ngày mới.
- Inputs v1.1 nhận `pause`, `shop_done`, `attack`, `photo` boolean; mở rộng chưa bật bỏ qua. `buy` chuỗi khác rỗng, chỉ chạy ở frame khai. Nút giữ xuyên pha không thành cạnh mới.
- Pause xét trước: bước vào chỉ tăng tick ngoài; đang pause bỏ buy/cạnh hành động. Resume chạy gameplay ngay bước đó. `sim_tick` và timer chỉ tiến khi gameplay chạy.
- Live có màn trình bày menu/intro/result/summary bên ngoài mô phỏng; headless chạy thẳng các pha Contract. UI đọc snapshot, không tính luật/giá/nâng cấp riêng.
- Cá sấu đọc tốc độ, miền sâu, khoảng cách, recoil, bất tử và tỷ lệ rơi từ tuning. Bước cuối recoil vẫn miễn hit/phát hiện; bước sau mới patrol/chase.
