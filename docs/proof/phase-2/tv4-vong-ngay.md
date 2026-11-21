# TV4 · Vòng ngày, pause và Shop

Chạy `PYTHONPATH=tests:. python3 -m unittest tests.test_day_cycle -v` để kiểm tra fixture TV4. Bộ đầy đủ `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` đạt **68/68**, gồm 7 test TV4. Test HTTP dùng cổng localhost tạm thời.

| Ca | Kết quả |
|---|---|
| Một ngày rút ngắn | Tick 0 phát `day_start → day_plan → phase_start`. Tick 1 chuyển quán với đúng kho từ `gather_end`. Tick 2 mở Shop, `days_completed` vẫn bằng 0. Tick 602 đóng Shop do hết giờ và hoàn tất ngày. |
| Hai ngày, mua oxy đúng giá ở bước cuối Shop | Tick 602 thu đúng 200, phát `bought` trước `shop_end(done)`. Ngày 2 bắt đầu với 2700/2700 tick oxy, money 0, earned 200 và score 500. Chạy lặp cùng seed và input cho các dòng JSONL giống nhau. |
| Hai cấp Máu và thu nhập qua ngày | Sau thanh toán ca tối, mua áo phao lần lượt giá 250 và 500. Lệnh mua thêm báo `max_level`; lệnh lạ báo `unknown`. Ngày 2 có 5/5 Máu, money 0, earned 750 và uy tín 3.2. |
| Pause trong Shop và hai mode độc lập | Tick ngoài vẫn tăng. Timer, sim_tick và phase_tick đứng yên. Lệnh mua trong pause bị bỏ và giữ nút đóng Shop tới lúc resume không tạo cạnh mới. Bước resume chạy gameplay ngay. |
| Kế hoạch và ngất | Tính lại nguyên liệu cho lẩu mắm. Ngất vẫn mở quán với kho rỗng. Nếu có cá lóc nhưng kế hoạch chỉ có lẩu mắm, khách phát `no_dish`. |
| Dữ liệu sai | Mã 2 cho cờ và fixture sai, kể cả khi đơn chỉ phát hiện thiếu nguyên liệu sau bàn giao kho. Output ngày chỉ được công bố sau khi chạy thành công. |

Smoke với manifest mặc định trên máy làm việc:

```sh
python3 -m chonoi.headless --mode day --seed 42 --ticks 22200 --out /tmp/tv4-day-default.jsonl
python3 -m chonoi.headless --mode day --seed 42 --days 5 --ticks 111000 --out /tmp/tv4-day5.jsonl
```

Lượt 1 ngày trả `days_complete` ở tick 22.200, `days_completed: 1`. Lượt 5 ngày trả `days_complete` ở tick 111.000, `days_completed: 5`. Đây là smoke phần vòng ngày trên cây làm việc. Cá và Cá Sấu Phase 2, bố trí thêm bếp/bàn và UI vòng ngày còn chờ tích hợp theo phân công.

Regression Phase 1 vẫn kiểm mode và nút lạ trả mã 2. Smoke thay `day` và `attack` trong danh sách dữ liệu lạ vì v1.1 đã công nhận hai tên đó. [Test TV4](../../../tests/test_day_cycle.py)
