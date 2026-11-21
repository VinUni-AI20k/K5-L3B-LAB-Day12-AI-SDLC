# Ma trận truy vết Phase 3

| Yêu cầu P3-03 | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Ticket-03 §1 · kho theo ID | Headless Quán v1.2 nạp mảng cá thể gồm hàng ươn, giữ độ tươi khi nạp và từ chối kho đếm/fixture sai | [Kiểm chứng P3-03](../proof/phase-3/quan-stock.md) | Đạt ở Quán |
| Ticket-03 §1 · hao tươi và giữ chỗ | Kiểm ngưỡng đúng tick, thứ tự ID, pause, giữ cá thể tươi nhất, claim trùng và thứ tự giữ lại | [Test](../../tests/test_restaurant_stock.py) | Đạt |
| Ticket-03 §1 · định giá theo độ tươi | Kiểm thứ tự `spoiled` → `dish_ready` → `cook_started`, cá thể bếp tiêu và giá đã chốt | [Kiểm chứng P3-03](../proof/phase-3/quan-stock.md) | Đạt |
| Ticket-03 §1 · bàn giao Gather → Quán → Shop | Cho Quán nhận dữ liệu đầu ra mẫu của Gather ở cùng tick và kiểm tồn cá thể qua Shop | [Test](../../tests/test_restaurant_stock.py) | Đạt ở đầu nhận và Shop. Smoke với đầu ghi thật chờ ghép Lặn v1.2. |
