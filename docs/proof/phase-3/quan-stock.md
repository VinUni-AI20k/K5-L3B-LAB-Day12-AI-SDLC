# Kiểm chứng kho và giữ chỗ ở Quán

Chạy trên Windows ngày 2026-11-21 với manifest chung v1.2 và phần hao tươi của Gather. Toàn bộ **201/201 test qua**, gồm **9 test P3-03** và test bàn giao kho giữa hai tiến trình headless.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python -c "import sys, unittest, helpers; original = helpers.headless_cmd; helpers.headless_cmd = lambda: [sys.executable, *original()[1:]]; suite = unittest.defaultTestLoader.loadTestsFromNames(['test_restaurant_stock', 'test_inventory_v12.InventoryV12.test_two_process_handoff_preserves_id_and_fresh']); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())"
```

Chạy toàn bộ hồi quy trên Windows bằng trình Python đang chạy unittest, vì alias `python3` trên máy trỏ tới Microsoft Store.

```powershell
python -c "import sys, unittest, helpers; original = helpers.headless_cmd; helpers.headless_cmd = lambda: [sys.executable, *original()[1:]]; result = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests')); sys.exit(not result.wasSuccessful())"
```

| Ca kiểm tra | Kết quả quan sát |
|---|---|
| Khách tự đặt | Chọn I3 tươi nhất trước. I2 và I10 cùng độ tươi, I2 được chọn trước. Sau ba đơn, lượt sau phát `no_dish`. |
| Qua ngưỡng | I2 và I10 bắt đầu ở 30, phát `spoiled` theo thứ tự I2 rồi I10 ở tick 1. I1 bắt đầu ở 30,25, vẫn dùng được ở tick 60 và phát `spoiled` ở tick 61. |
| Tranh phần giữ thay thế | Hai đơn cùng tick ở T1 rồi T2 nhận hai cá thể thay thế. Đơn đến muộn ở T3 chuyển `unfulfillable` và rời đúng tick 3. |
| Giữ lại và nấu | Cùng tick phát `spoiled`, `dish_ready`, `cook_started`. Bếp tiêu đúng I1 và I2 và chốt giá canh chua là 85 nghìn đồng. |
| Kho v1.2 ở CLI | File cá thể giữ đủ ID, loại và độ tươi ở tick 0, kể cả I10 có fresh 29,9999. Kho đếm và các fixture sai trả mã 2 trước khi tạo JSONL. |
| Bàn giao bằng file | Gather chạy qua CLI, xuất kho cá thể. Một tiến trình Quán đọc lại và có đúng ID, loại, độ tươi như `gather_end` ở tick 0. |
| Quán và Shop | Trong Day, đầu ra thật của Gather xuất hiện ở tick 0 của Quán với fresh giữ nguyên. Sau một tick Quán, Shop nhận đúng tồn còn lại và giữ độ tươi xuyên 60 tick. |

Smoke trọn một ngày với `python -m chonoi.headless --mode day --days 1 --seed 17 --ticks 22200 --out day.jsonl` phát một lần `gather_end`, `quan_end` và `shop_end`. Kết thúc ở tick 22.200 với `reason=days_complete` và `days_completed=1`.
