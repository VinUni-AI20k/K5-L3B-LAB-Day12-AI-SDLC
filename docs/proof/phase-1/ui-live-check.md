# Bằng chứng kiểm chứng UI chơi trực tiếp — Phase 1 (`client/ui`, `duhocsinh4to10`)

## Phạm vi kiểm chứng
- File nâng cấp: [`chonoi/web/index.html`](../../../chonoi/web/index.html) (chỉ đọc snapshot từ `GET /state`, gửi input qua `POST /input` và `POST /restart`, không chứa logic mô phỏng, tắt hoàn toàn ở `chonoi.headless`).
- Tích hợp đầy đủ sau khi đồng bộ `origin/main` (`52f0245`): hỗ trợ `--extra-content`, sprite atlas `/assets/cho-noi-sprites.png`, animation bơi 6 khung `/assets/ut-sen-swim.png`, cùng luật thật từ `gather.py` (Lát 1–2) và `quan_service.py` (Lát 4, hiển thị `order_id` trên bếp/tay và viền bàn giao món).

## Tính năng HUD đã hiển thị
- **`gather` (Buổi sáng):** đồng hồ đếm ngược, thanh Oxy (phân vùng mặt nước / dưới nước / cạn oxy + thanh đếm ngạt `zero_oxy_ticks`), tim Máu (`hp/hp_max`, trạng thái `invuln_ticks`), giỏ LIFO từng ô có đánh dấu đỉnh mới nhất + cảnh báo đầy giỏ, trạng thái nút hái (vòng đếm ngược mọc lại `regrow_ticks`), đàn cá (kèm sản lượng `fish_yield`), tọa độ & tốc độ, hồi chiêu `catch_cd_ticks`, gợi ý phím `[E]`/`[Space]`.
- **`quan` (Buổi tối):** đồng hồ ca, tiền / thu nhập / uy tín (5 sao) / điểm, món đang cầm trên tay (`hand`, kèm mã đơn `order_id`), trạng thái bếp (`idle`/`cooking` có thanh tiến độ/`ready` có `ready_ticks`/`burned`), bàn & khách (gọi món, thanh kiên nhẫn kèm mốc boa `tip_min_patience_ratio`, tiến độ ăn `eat_ticks_left`), kho nguyên liệu (gồm phần giữ chỗ `reserved` nếu có) và thực đơn nhanh (tự mở rộng thêm 3 món khi có `--extra-content`).
- **Tiện ích chung:** phím `e.code` chống kẹt bộ gõ tiếng Việt (Telex/UniKey), ngăn Nhật ký sự kiện (`H`), âm thanh Web Audio tùy chọn tắt mặc định (`M`), popup sự kiện nổi, modal tổng kết + nút Chơi lại (`R`).

## Kết quả chạy kiểm thử
- `python -m unittest tests.test_smoke_p1 tests.test_python_starter_units tests.test_team_check tests.test_ui_live tests.test_gather tests.test_quan_service -v`: **71/71 pass** (không phá Test Contract headless hay tính tất định).
- `python -m unittest tests.test_live -v`: **1/1 pass** → Tổng **72/72 pass**.
- `python tools/check_team.py`: `OK: 6 thành viên`.
- Script kiểm thử render JS trên Node v22 (giả lập Canvas2D & DOM cho snapshot `gather`, `quan`, `fainted`, `quan_end`, `--extra-content`, và nhập phím `KeyW` với `key="ư"`): **PASS toàn bộ**.
