# Research — Phase 2

| # | Quyết định | Lý do | Loại bỏ |
|---|---|---|---|
| R1 | Giữ starter Python; thêm `chonoi/sim/day.py` (máy trạng thái pha) và `chonoi/sim/shop.py`; `GatherSim`/`QuanSim` nhận thêm tham số Ngày (cấp hiệu lực, kế hoạch, bố trí quái) | Tái dùng sim độc lập cho `day`, không nhân đôi luật | Viết lại sim riêng cho day |
| R2 | Bàn giao kho trong bộ nhớ: `QuanSim(..., inventory=gather.inventory_items())` | Đề cho phép; cùng schema v1.0 | Ghi file tạm |
| R3 | Pause xử lý ở tầng runner/day trước khi gọi `sim.step` | Đề: vào pause chỉ tăng `tick` ngoài, `sim_tick`/`phase_tick` đứng | Mỗi sim tự xử lý pause |
| R4 | `tick` (ngoài) ≠ `sim_tick` (không tính bước pause) ≠ `phase_tick` (reset 0 mỗi pha) | Đề §4.2, §4.4 | Một bộ đếm |
| R5 | RNG luồng riêng: `fish_turn`, `fish_spawn`, `quan_order` (GIẢ ĐỊNH tên); không reset theo Ngày | Thêm luồng không làm lệch luồng khác | Một luồng chung |
| R6 | Cá Sấu: dữ liệu `gather.monsters.species.ca_sau` + `spawns[]` có `from_day` | Đề §4.1; mở rộng snake chỉ thêm loài | Hard-code M1/M2 |
| R7 | Sửa file khung (`headless`, `inputs`, `inventory`, `contract`, `scenario`, `runner`) có kiểm soát: một người (TV6+TV5 cho CLI/inputs, TV1 cho contract/inventory), báo cả nhóm | Bắt buộc để có `day`, `--days`, nút mới, 6 nguyên liệu | Viết entry point khác (vẫn phải qua `headless_cmd`) |
| R8 | Hiệu năng: duyệt cá/quái O(n) mỗi bước (n ≤ 12+2) → một Ngày 22 200 bước dư sức ≤ 20 s | Đề §2 | Tối ưu sớm |
| R9 | Đề xuất mở rộng phase sau: `burn` (chỉ thêm `ready_ticks` > 1200 → bỏ món), `snake` (thêm loài `ran` + M3, dùng chung luật quái) | Rẻ nhất trên nền lõi P2 | weapon/net/vendor/ca_ho tốn hơn |
