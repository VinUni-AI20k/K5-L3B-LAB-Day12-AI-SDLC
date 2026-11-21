# Kiểm chứng phần khách và kho

Chạy trên Windows ngày 2026-11-21. Bộ test hiện có qua 38/38, gồm 6 test phần khách và kho. Trong lần chạy test, lời gọi headless dùng Python đang chạy unittest vì `python3` trên máy trỏ vào alias Microsoft Store. Smoke test hai tiến trình ở mục G cũng qua.

```powershell
$env:PYTHONPATH = 'tests;.'
python -c "import sys, unittest, helpers; original = helpers.headless_cmd; helpers.headless_cmd = lambda: [sys.executable, *original()[1:]]; result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests')); sys.exit(not result.wasSuccessful())"
python -m chonoi.headless --mode quan --seed 17 --ticks 3720 --snapshot-every 120 --inventory docs/contracts/inventory.sample.json --out quan.jsonl
```

Kết quả quan sát trong JSONL với kho mẫu.

| Tick | Kết quả |
|---|---|
| 0 | Tồn vật lý có 2 bông súng và 1 cá lóc. Chưa có khách. |
| 120 | C1 đến T1, gọi gỏi bông súng và giữ 2 bông súng. Tồn vật lý giữ nguyên, lượng khả dụng còn 1 cá lóc. |
| 3720 | `customer_left` của C1 có lý do `patience` và uy tín 2,5. Phần giữ được nhả. `customer_arrived` của C2 theo sau trong cùng tick, vào T1 và giữ 1 cá lóc. |

Khi ghép lát bếp, chạy lại trường hợp phục vụ đúng tick kiên nhẫn về 0 và đúng tick đóng ca. Bước tương tác chạy sau giảm kiên nhẫn và trước duyệt khách theo ID bàn để trả tiền hoặc rời bàn. HUD tính số khả dụng từ `stock` trừ tổng `customers[].reserved`.
