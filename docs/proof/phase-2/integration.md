# Kiểm chứng vòng ngày và bàn giao kho

Chạy trên Windows ngày 2026-11-21, seed 17.

```powershell
python -m chonoi.headless --mode day --days 1 --seed 17 --ticks 22200 --snapshot-every 1000 --out day.jsonl
python -m chonoi.headless --mode day --days 5 --seed 17 --ticks 111000 --snapshot-every 1000 --out five-days.jsonl
```

| Lượt | Kết quả |
|---|---|
| Một ngày, không thao tác | Tick 10.800 chuyển Gather → Quán. Tick 21.600 mở Shop. Tick 22.200 Shop đóng với `time`, `days_completed: 1`, `reason: "days_complete"`. Thời gian đo trên máy thử khoảng 0,37 giây. |
| Năm ngày, không thao tác | Tick 111.000 hoàn tất, `days_completed: 5`. Thời gian đo trên máy thử khoảng 1,34 giây. |
| Hai tiến trình Gather → Quán | Fixture giỏ có 1 cá lóc, 2 bông súng, 1 cá kèo và 1 kèo nèo. Cập bến ở tick 1. File kho và `stock` của Quán tại tick 0 đều có `{"bong_sung":2,"ca_keo":1,"ca_loc":1,"keo_neo":1}`. |
| Nối bếp với Shop | Cập bến tick 1. Nấu ở tick 3, món chín và bưng ở tick 363, phục vụ tick 502, trả 72 ở tick 1102. Tick 1202 dùng đúng 200 tiền để mua bình oxy rồi đóng Shop. Ngày 2 bắt đầu với 2.700 tick oxy và `earned: 200`. |
| Ngất khi đang có hàng | Ở tick 1, Gather phát `choke`, `faint`, `gather_end`. Quán mở cùng tick với `phase_tick: 0` và kho rỗng. |

**114/114 test qua** sau khi đồng bộ Phase 1 từ `main`, gồm 12 test của P2-03. Lệnh hồi quy trên Windows dùng trình Python chạy unittest cho tiến trình headless vì alias `python3` trên máy trỏ tới Microsoft Store.

```powershell
$env:PYTHONPATH = 'tests;.'
python -c "import sys, unittest, helpers; original = helpers.headless_cmd; helpers.headless_cmd = lambda: [sys.executable, *original()[1:]]; result = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests')); sys.exit(not result.wasSuccessful())"
```

## Giao diện tích hợp

- Headless phát `day_start`, `day_plan`, `phase_start` trước snapshot Ngày mới. `day_plan` có món, số suất và lượng cần thu. UI có thể lấy mốc này để hiện DayIntro.
- `gather_end` mang đúng kho đầu vào của Quán. `gather_end` và `phase_start(quan)` ở cùng tick để UI hiện EveningIntro mà không làm lệch lịch khách.
- Đọc `served`, `paid`, `customer_left` và `quan_end` để tổng hợp DayResult trước giao diện Shop. Snapshot Shop giải thích riêng cấp đã mua bằng `upgrades` và cấp đang hiệu lực bằng `active_upgrades`.
- Khi chạy không có fixture, đầu ngày bắt đầu với giỏ rỗng và oxy/Máu đầy. Scenario `gather` được áp lại mỗi ngày theo mục 4.3, nên fixture có thể đặt giỏ và trạng thái khác mặc định.
