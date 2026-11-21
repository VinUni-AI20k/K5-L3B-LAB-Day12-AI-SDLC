# TV3 · Kiểm chứng khách và lịch spawn

Chạy `PYTHONPATH=tests:. python3 -m unittest tests.test_quan_customers -v` sau khi ghép với TV4 trên `main`. Kết quả 6/6 test đạt.

| Ca theo PRD-0 / phan-cong TV3 | Kết quả |
|---|---|
| Fixture thiếu `reserved` | Cấp theo recipe món; state=`waiting`, order_status=`reserved`, patience đầy (3600). |
| Bàn bận ở tick spawn | Bỏ lượt — không `customer_arrived`, không `no_dish`. |
| Kho không đủ món | Phát `no_dish` tại tick 120; không sinh khách. |
| Spawn thành công | `customer_arrived` tick 120; reserved khớp recipe; patience giảm từ bước sau (3600 → 3599). |
| Patience về 0 (đơn assigned + bếp) | `customer_left` reason=`patience`, uy tín −0.5; dọn bếp cùng order_id. |
| Hết ca còn waiting | `customer_left` reason=`closing`, uy tín giữ nguyên; rồi `quan_end`. |

[Test headless của TV3](../../../tests/test_quan_customers.py)

API TV3 trên cây ghép TV4: `available_stock`, `try_spawn_customer` (RNG `dish_pick`); leave/cook do TV4 (`_leave`, bếp).
