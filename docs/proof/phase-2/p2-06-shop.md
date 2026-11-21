# Kiểm chứng P2-06, AC-P2-05

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` — **188/188 đạt** trên nhánh Shop. Năm test P2-06 kiểm mua đúng giá theo cấp, từ chối khi thiếu tiền hoặc đạt trần, lệnh lạ, mua ở tick cuối và hiệu lực từ ngày kế.
- Ghép mã Shop với `p2-03-fish-dynamics` trong bản sao tạm — **195/195 test đạt**.
- Trên bản ghép, `python3 tools/check_determinism.py --seed 17 --ticks 4500` và `python3 tools/check_no_hardcode.py` đều đạt.

## Giao diện cho P2-07

Khi mở Shop, dựng `ShopSim(tuning, money=..., earned=..., reputation=..., stock=..., upgrades=...)` từ ca quán. Mỗi tick gameplay gọi `shop.step(buy=..., done=...)` với lệnh mua ở frame hiện tại và cạnh lên của `shop_done`. Khi pause, không gọi `step`. Hàm trả danh sách cặp `(event_name, data)` theo thứ tự mua trước đóng. `snapshot()` trả thời gian, tiền, thu nhập, uy tín, kho và cấp đã mua, phục vụ snapshot chung của `day`.

Khi bắt đầu ngày sau, sao `shop.upgrades` sang `active_upgrades`, rồi truyền `apply_gather_upgrades(tuning, active_upgrades)` cho `GatherSim`. Hàm tạo tuning mới cho buổi sáng, và ca sáng khởi tạo oxy và Máu đầy. P2-07 quản lý đổi pha, `days_completed` và map cấp đang có hiệu lực. P2-06 kiểm phần Shop độc lập và việc áp cấp vào `GatherSim`.
