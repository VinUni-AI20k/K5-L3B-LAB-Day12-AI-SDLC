# Kiểm chứng spec Phase 1

- Bảng trong `TEAM.md` có đúng bốn module, mỗi module có một mục Phase 1, khớp `team_size`. Các liên kết nội bộ mở được. `check_team.py` còn cần tên và GitHub handle thật của cả bốn thành viên.
- Các suite `tests.test_smoke_p1`, `tests.test_python_starter_units` và `tests.test_team_check` đạt 31/31. Trên Windows dùng `python3.exe` tạm từ Python 3.12 để khớp `headless_cmd`. `python -m unittest tests.test_live -v` đạt 1/1 khi chạy ngoài sandbox để kết nối localhost. Đây là kết quả trên starter dùng lúc lập spec.
- Lệnh smoke hai tiến trình trong `TEAM.md` đạt. Với seed 42, gather xuất kho khớp `gather_end.data.inventory`, quan nạp kho đó và thấy `bong_sung: 2`, `ca_loc: 1` ở snapshot tick 0.
- Hai lệnh headless trong `TEAM.md` với seed 1 và giới hạn 600 tick đều thoát mã 0 và ghi dòng `end` ở tick 600. Mode `quan` nạp `docs/contracts/inventory.sample.json`.

## Kiểm chứng giao diện dùng chung

- Đã đối chiếu 19 tên sự kiện với mục E, đọc thử mẫu JSON, kiểm mã món và nguyên liệu theo tuning và kiểm liên kết từ `AGENTS.md` tới spec.
- Chạy lại các suite `tests.test_smoke_p1`, `tests.test_python_starter_units`, `tests.test_team_check` với alias `python3` tạm trên Windows và `tests.test_live` với localhost. Tổng cộng 32/32 test đạt trên starter. Kết quả này là kiểm tra baseline khi cập nhật đặc tả.
