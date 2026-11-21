# Phase 2 — Quán và menu theo ngày

TV4 có thể mở Quán qua `Session("quan", tuning, scenario, seed, inventory=inventory, day_dishes=plan["dishes"])`. `Session` chuyển tiếp hai tham số cho `QuanSim`. Quán độc lập mặc định dùng toàn bộ menu.

Đã chạy `python -m unittest discover -s tests` trong thư mục bản nhóm, với `PYTHONPATH=tests;.`, `PYTHONUTF8=1` và bản sao Windows launcher `py.exe` tên `python3.exe` trong PATH tạm để test gọi được lệnh trong manifest. **59 test qua**.

Test mới xác nhận manifest có 2 bếp, 4 bàn và 6 món. Với kho gồm cá lóc và cá kèo, khách D1 chỉ gọi cá lóc nướng trui và nguyên liệu cá kèo còn nguyên. Với kho chỉ có cá kèo, D1 phát `no_dish`, còn Quán độc lập nhận đơn cá kèo nướng.

Luồng CLI `--mode day` chờ TV4 tích hợp. Ý nghĩa số lượng trong kế hoạch ngày được ghi ở Q8 trong `docs/clarify.md`.
