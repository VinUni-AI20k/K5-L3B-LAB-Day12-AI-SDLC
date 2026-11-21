# Bằng chứng triển khai Module sim/quan (Lát 3 & 4 - Phase 1)

**Người thực hiện:** Nguyễn Văn Lâm (`sim/quan` · Integrator)  
**Phạm vi** · [chonoi/sim/quan.py](../../../chonoi/sim/quan.py), [chonoi/scenario.py](../../../chonoi/scenario.py), [tests/test_quan.py](../../../tests/test_quan.py).

## 1. Các hạng mục đã hoàn thành

1. **Khách, giữ chỗ và kiên nhẫn (Lát 3):**
   - Khách tự sinh đến theo lịch `first_customer_tick` (120) và chu kỳ `customer_interval_s * 60` khi còn thời gian.
   - Bàn bận: bỏ lượt.
   - Bàn trống: tính kho khả dụng (`stock - sum(c.reserved)`). Nếu không đủ món nào thì phát event `no_dish` với `{}`. Nếu đủ, chọn món theo seed ngẫu nhiên (`self.rng.get("customer")`), cấp `order_id` họ `C`, giữ đúng công thức vào `reserved` và phát `customer_arrived`.
   - Đếm ngược kiên nhẫn (`patience_ticks_left`). Khi hết kiên nhẫn, khách bỏ đi (`customer_left`, reason: `patience`), giảm uy tín 0.5 điểm (`left_reputation_delta`), nhả nguyên liệu đã giữ.

2. **Bếp, phục vụ và tiền (Lát 4):**
   - Tương tác E: ưu tiên đối tượng trong bán kính `interact_radius` theo `(khoảng cách, bếp trước bàn, ID)`.
   - Bếp `idle`: nhận đơn `reserved` cũ nhất của khách, trừ nguyên liệu tồn vật lý trong kho, phát `cook_started` kèm `items` và `base_price`.
   - Bếp `cooking`: đếm ngược `cook_ticks_left`. Khi chín chuyển sang `ready` và phát `dish_ready`.
   - Bếp `ready`: bưng món lên tay khi tay trống (`hand is None`), phát `dish_picked`.
   - Giao bàn: người chơi đến bàn khách có món trên tay khớp `order_id`, phát `served`. Tính boa lúc giao: nếu kiên nhẫn còn lại $\ge 50\%$, tiền boa = $20\%$ giá món. Khách chuyển sang trạng thái `eating`.
   - Khách ăn xong: đếm ngược `eat_ticks_left`. Hết giờ ăn thì thanh toán (`paid`, reason: `finished_eating`), thu tiền gốc + tiền boa, cộng doanh thu và cộng uy tín 0.2 (`tip_reputation`) nếu có boa.
   - Hết ca (`time_left_ticks <= 0`): thu tiền khách đang ăn (`paid`, reason: `closing`), dọn khách chờ (`customer_left`, reason: `closing`), phát `quan_end` với reason `time`.

3. **Kiểm tra fixture & mâu thuẫn (Mục D):**
   - Bổ sung kiểm tra `scenario.py` cho khối `quan`: món ở khách/bếp/tay phải thuộc `menu`, khách giữ chỗ nguyên liệu không được vượt tồn kho (nếu có `stock`).

## 2. Kết quả kiểm thử

Chạy toàn bộ test suite:
```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -v
```
Kết quả: **41/41 test PASSED (OK)** trong đó có 9 test case mới trong `test_quan.py` bao quát mọi nhánh của Lát 3 & 4:
- `test_quan_snapshot_structure`: Cấu trúc snapshot chuẩn (bổ sung `player.vel`).
- `test_customer_arrival_and_reserved`: Khách đến đúng tick 120, giữ chỗ nguyên liệu.
- `test_no_dish_when_out_of_stock`: Bàn trống thiếu nguyên liệu phát `no_dish`.
- `test_table_busy_skips_new_customer`: Bàn bận bỏ lượt khách.
- `test_customer_impatient_leaves`: Khách hết kiên nhẫn rời quán, trừ uy tín.
- `test_full_service_cycle`: Chu trình toàn vẹn từ gọi món -> nấu -> chín -> bưng -> giao bàn -> ăn xong -> thanh toán có boa.
- `test_serve_on_boundary_tick_succeeds`: Phục vụ đúng tick kiên nhẫn chạm 0 thành công.
- `test_closing_clears_customers_and_pays_eating`: Đóng ca xử lý khách đang ăn và khách chờ đúng quy ước.
- `test_headless_quan_run_deterministic`: Chạy headless 150 tick qua file kho mẫu, byte xuất ra tất định 100%.
