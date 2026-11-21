# TV3 · Kiểm chứng khách và giữ chỗ nguyên liệu

Chạy `PYTHONPATH=tests:. python3 -m unittest tests.test_quan_customers -v` trên bản triển khai TV3. Kết quả 6/6 test đạt.

| Ca theo PRD-0 / phan-cong TV3 | Kết quả |
|---|---|
| Fixture thiếu `reserved` | Cấp theo recipe món; state=`waiting`, order_status=`reserved`, patience đầy (3600). |
| Bàn bận ở tick spawn | Bỏ lượt — không `customer_arrived`, không `no_dish`. |
| Kho không đủ món | Phát `no_dish` tại tick 120; không sinh khách. |
| Spawn thành công | `customer_arrived` tick 120; reserved khớp recipe; patience giảm từ bước sau (3600 → 3599). |
| Patience về 0 | `customer_left` reason=`patience`, uy tín −0.5; nhả reserved; dọn bếp/tay cùng order_id; stock vật lý không hoàn thêm. |
| Hết ca còn waiting | `customer_left` reason=`closing`, uy tín giữ nguyên; rồi `quan_end`. |

[Test headless của TV3](../../../tests/test_quan_customers.py)

API bàn giao TV4: `available_stock`, `normalize_customer`, `release_and_cleanup`, `tick_patience`, `handle_patience_leave`, `handle_closing_leaves`, `try_spawn_customer`.
