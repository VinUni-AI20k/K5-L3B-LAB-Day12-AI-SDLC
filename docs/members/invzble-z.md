# invzble-z — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Giữ vai trò Integrator: rà soát quy trình nhóm, cấu hình `game.contract.json`, hợp nhất các PR của các thành viên.
  - Cập nhật Test Contract v1.1 cho Phase 2 (`game.contract.json`, `chonoi/contract.py`): 6 món ăn, 2 bếp, 4 bàn, bổ sung `keo_neo`, cấu hình quái vật Cá Sấu, kế hoạch `day_plan` và hệ thống nâng cấp Shop.
  - Triển khai Lát 4a (`sim/day.py`, `runner.py`, `inputs.py`, `headless.py`, `tests/test_p2_day.py`): chế độ `--mode day --days N`, vòng ngày Gather -> Quán -> Shop, bàn giao kho bộ nhớ, Shop (mua nâng cấp oxygen/hp, `bought`/`buy_failed`/`shop_end`), cơ chế pause/resumed, `active_upgrades` áp dụng ngày kế tiếp.
- Tôi đã review (kèm link):
  - Review và merge PR #3 (`p1/quan-lat4` của Kiên), PR #4 (`HoangMinh` của Minh), nhánh `origin/NguyenQuangDung` của Dũng và nhánh `origin/Quoosc` của Quốc.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Khi cập nhật `game.contract.json` thêm loại cây `keo_neo`, ban đầu hàm `_validate_gather` trong `chonoi/contract.py` chỉ cho phép `bong_dien_dien` và `bong_sung` nên sẽ báo lỗi `BadInput`. Tôi phát hiện qua việc đối chiếu logic kiểm tra hợp đồng trước khi lưu file cấu hình.
  - Khi viết `DaySim`, import `from .sim.gather` trong module `chonoi.sim` gây `ModuleNotFoundError: No module named 'chonoi.sim.sim'`. Phát hiện qua chạy unittest và sửa thành relative import `from .gather`.
- Điều tôi học được:
  - Tầm quan trọng của việc chốt Test Contract và giao diện chuyển pha từ sớm để các nhánh làm việc song song không bị xung đột; cơ chế lock contract giúp kiểm soát độ ổn định của toàn hệ thống.
