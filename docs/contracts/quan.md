# Hợp đồng quán (`quan`) — TV2 soạn theo PRD-0 mục D/E/F, chờ TV1 (Integrator) và TV3 duyệt

> Nguồn: [`docs/prd/PRD-0.md`](../prd/PRD-0.md). Câu còn mở: [`docs/clarify.md`](../clarify.md) Q14–Q19. Đổi gì ở đây phải báo TV3.

## Khách (`snapshot.customers[]`, sắp theo id, chỉ khách còn ngồi)

| Trường | Kiểu | Ai ghi | Ghi chú |
|---|---|---|---|
| `id` | `"C<n>"` | lát 3 | = `order_id` của đơn; cấp bằng `IdAllocator.new("C")` |
| `table_id` | id bàn | lát 3 | bàn trống id nhỏ nhất |
| `dish_id` | id món | lát 3 | chọn đều theo seed trong món đủ nguyên liệu khả dụng |
| `order_tick` | int | lát 3 | phase_tick lúc gọi (fixture mặc định 0) |
| `state` | `waiting` \| `eating` | lát 3 → lát 4 | lát 4 đổi sang `eating` khi `served` |
| `patience_ticks_left` | int | lát 3 | chỉ giảm khi `waiting`, giảm từ bước sau khi gọi |
| `eat_ticks_left` | int | lát 4 | 0 khi chưa ăn |
| `order_status` | `reserved` \| `assigned` \| `unfulfillable` \| `served` | lát 3 → lát 4 | `reserved` khi gọi; lát 4 → `assigned` khi bắt đầu nấu, → `served` khi phục vụ |
| `reserved` | `{kind: số}` | lát 3 → lát 4 | = công thức khi `reserved`; lát 4 đặt `{}` khi bắt đầu nấu (đồng thời trừ `stock`) |
| `base_price`, `tip` | int \| null | lát 4 | `null` tới khi chốt (Q14) |

**Payload món** (bếp `dish`, `hand`): `{order_id, dish_id, base_price}`.
**Kho:** `stock` = tồn vật lý gồm cả phần giữ. Khả dụng = `stock − Σ reserved`.

## Hàm lát 3 cung cấp cho lát 4 (`chonoi/sim/quan.py`)

| Hàm | Dùng khi |
|---|---|
| `available_stock()` | cần kho khả dụng |
| `add_reputation(delta)` | boa dương: `+tip_reputation` (đã kẹp min/max) |
| `remove_customer(c)` | khách rời sau `paid`: tự nhả phần giữ, bỏ món của đơn trên bếp/tay |
| `_settle_customers` | chỗ `TODO(lát 4 — TV3)` cho `paid` (finished_eating / closing) |
| `phase_tick`, `patience_max_ticks`, `to_ticks(s)` | tiện ích |

## Thứ tự một bước (`QuanSim.step`, PRD-0 F "Quán")

1. phase_tick+1, timer ca−1, *(TV3: nấu, ăn, ready_ticks)*, kiên nhẫn−1 (lát 3)
2. *(TV3: bếp theo id, nấu xong → ready, `dish_ready`)*
3. di chuyển → *(TV3: tối đa một interact: `cook_started` / `dish_picked` / `served`)*
4. theo id bàn: *(TV3: `paid`)* · khách waiting hết kiên nhẫn → `customer_left patience` (uy tín +`left_reputation_delta`) · hết ca → `customer_left closing` (không trừ uy tín) → `quan_end`
5. còn giờ: lượt khách → `customer_arrived` / `no_dish {}`

## Sự kiện lát 3

| Tên | `data` |
|---|---|
| `customer_arrived` | `{order_id, table_id, dish_id}` |
| `no_dish` | `{}` |
| `customer_left` | `{order_id, table_id, reason: patience\|closing, reputation}` (uy tín sau khi đổi) |

## Fixture `quan` → mã 2 (đã cài trong `chonoi/scenario.py` + `QuanSim`)

Trường lạ; `dish_id` thiếu/ngoài menu; `state`/`order_status` lạ; bộ đếm âm hoặc vượt trần (kiên nhẫn, ăn, nấu); `reserved` khác công thức (đơn reserved) hoặc khác rỗng (đơn khác);
**giữ quá tồn** (kể cả kho từ `--inventory`); eating ⇔ served; eating thiếu `eat_ticks_left` dương / `base_price` / `tip`; không eating mà `eat_ticks_left > 0`;
đơn assigned không có đúng một món ở bếp hoặc tay; món trỏ đơn không có thật / không assigned / sai `dish_id`; bếp và tay giữ cùng đơn;
payload sai dạng; bếp idle có món hoặc timer, cooking timer ngoài `[1, cook_s]`, ready có `cook_ticks_left`; id bếp/bàn cập nhật không tồn tại; `pos` ngoài miền;
`reputation` ngoài `[min, max]`; `random_customers` không phải boolean.
