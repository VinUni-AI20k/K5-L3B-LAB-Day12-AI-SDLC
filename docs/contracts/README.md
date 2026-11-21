# Hợp đồng tích hợp (nên chốt sớm; hình thức do nhóm chọn)

Điền trong 15 phút kickoff (hoặc thay bằng một mục trong README / một bảng trên giấy, miễn cả nhóm cùng thống nhất):
1. **Schema file kho** — khớp mục G của PRD-0 (kho ghi khi `gather_end`) + một file kho mẫu hợp lệ: `inventory.sample.json`.
2. **Giao diện giữa `sim/*` và `client/ui`** — trạng thái nào UI được đọc, lệnh nào UI gửi vào.
3. **Danh sách sự kiện** — tên, `data`, ai phát, ai nghe (gather: `gather`, `node_regrown`, `hold_full`, `fish_caught`, `gather_end`...; quan: theo mục E của PRD-0).

## Chia hàm theo lát (khung đã tạo sẵn, mỗi người chỉ sửa hàm của mình)

| Lát | File | Hàm sở hữu | Hàm dùng chung (sửa phải báo nhóm) |
|---|---|---|---|
| 1 | `chonoi/sim/gather.py` | `_update_oxygen` | `_add_to_hold` |
| 2 | `chonoi/sim/gather.py` | `_try_gather`, `_try_catch` | `_add_to_hold` |
| 3 | `chonoi/sim/quan.py` | `_init_customers`, `_tick_patience`, `_settle_customers`, `_close_shift`, `_spawn_customers`, `_leave` | `_change_reputation`, `_available`, `_reserve`, `_release` |
| 4 | `chonoi/sim/quan.py`, `chonoi/scenario.py` (`_validate_quan`) | `_tick_stoves_and_eating`, `_interact`, `_pay` | như lát 3 |

Thứ tự gọi trong `step()` do Integrator giữ; đổi phải đối chiếu PRD (gather mục F / Ticket-02 4.5, quán mục F).
Quán (PRD-0 mục F): đồng hồ + kiên nhẫn + nấu/ăn → di chuyển + tối đa một interact → theo id bàn: ăn xong trả tiền, hết kiên nhẫn rời (khi ca còn giờ) → hết ca thì `_close_shift` (khách ăn trả `closing`, khách chờ rời `closing`, `quan_end`) → còn giờ thì lượt khách mới.

## Cấu trúc khách (lát 3 tạo, lát 4 đọc/đổi) — theo PRD-0 mục D/F

| Trường | Kiểu | Ai ghi | Ghi chú |
|---|---|---|---|
| `id` | chuỗi | lát 3 | khách mới cấp `ids.new("C")`, nối sau id fixture; cũng là `order_id` |
| `table_id` | chuỗi | lát 3 | bàn trống id nhỏ nhất |
| `dish_id` | id món trong `menu` | lát 3 | chọn đều theo seed (stream `customer_dish`) trong món đủ nguyên liệu khả dụng |
| `order_tick` | số nguyên | lát 3 | `phase_tick` lúc đến |
| `state` | `waiting` / `eating` | lát 3 → lát 4 | lát 4 đổi sang `eating` khi `served` |
| `patience_ticks_left` | số nguyên | lát 3 | đầy = `patience_s × 60`, chỉ giảm khi `waiting`, bắt đầu từ bước sau khi đến |
| `eat_ticks_left` | số nguyên | lát 4 | 0 tới khi được phục vụ |
| `order_status` | `reserved` / `assigned` / `unfulfillable` / `served` | lát 3 → lát 4 | khách mới `reserved` |
| `reserved` | `{kind: số}` | lát 3 | = công thức món; stock chỉ trừ khi `cook_started` (lát 4 xóa `reserved`, đổi `assigned`) |
| `base_price`, `tip` | số nguyên hoặc `null` | lát 4 | `null` tới lúc chốt (xem `docs/clarify.md` #1) |

Món trên bếp / trên tay: payload `{order_id, dish_id, base_price}` (`docs/clarify.md` #2). Khách rời (`_leave`) bỏ món có `order_id` trùng.

Khi đổi hợp đồng sau này: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú, tùy chọn).
