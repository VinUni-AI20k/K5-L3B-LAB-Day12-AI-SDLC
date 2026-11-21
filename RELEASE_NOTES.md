# Quán Ăn Chợ Nổi v1.0.0

> Bản đã đối chiếu với code trên nhánh phát hành (tag `phase-4`).

## Có gì trong bản này
- **Một ngày trọn vẹn:** buổi sáng lặn và hái (`gather`), buổi tối mở quán (`quan`), rồi Shop. Chế độ `day` chạy một hoặc nhiều ngày (1 đến 10), kế hoạch D1–D5 lặp ở ngày 6–10.
- **Độ tươi nguyên liệu:** mỗi cá thể có độ tươi riêng. Hàng dưới 30% là ươn và không dùng để nấu. Có sự kiện `spoiled`.
- **Cá Sấu Năm Chèo:** tuần tra, đuổi người chơi, gây sát thương làm rơi một phần giỏ, có bất tử sau khi bị chạm.
- **Tạm dừng** (Esc hoặc P) và **Shop** nâng cấp bình oxy và áo phao.
- **Cảnh báo dễ nhận biết:** thủy quái gần, oxy sắp hết, khách sắp giận. Chế độ tương phản cao bật bằng phím C.
- **Benchmark có render:** `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json`.
- **Soak headless 10 ngày:** `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.

## Cách chạy
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Chơi trên trình duyệt: `python3 -m chonoi.live --mode gather` (hoặc `--mode quan`)
- Headless (đã chạy thử, thoát 0, kết thúc `days_complete`): `python3 -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --out out.jsonl`
- Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (cần Chrome, Chromium hoặc Edge; đặt `CHROME_BIN` nếu không tự tìm thấy)

Điều khiển: WASD hoặc mũi tên để đi và bơi, E để tương tác, Space để bắt cá, Esc hoặc P để tạm dừng, C để bật tương phản cao, R để chơi lại. Trong Shop: 1 mua bình oxy, 2 mua áo phao, Enter để xong.

Môi trường: Python 3 (chỉ thư viện chuẩn). Benchmark cần trình duyệt Chrome-based.

## Giới hạn đã biết
- **Chưa có** các mục sau (có trong đặc tả mở rộng nhưng không có trong code của bản này): dòng nước lũ, cá Hô (sổ tay), lưới và vợt hút cá, lao xua (weapon), rắn Hổ Mây, chợ Chú Sáu, chụp ảnh, bảng xếp hạng cục bộ, phụ đề âm thanh.
- **Khách đặt trước** có dữ liệu trong scenario nhưng chưa phát sự kiện `reservation_announced`, nên chưa chạy đầy đủ trong bản này.
- **Món cháy** có mã nhưng tắt mặc định (`burn_s` là `null` trong contract).
- **Benchmark** đo trên Windows với Chrome. Chưa đo trên macOS hoặc Linux.
- **Bot soak** hiện không điều khiển người chơi, nên soak chỉ kiểm vòng 10 Ngày không lỗi, chưa kiểm gameplay.
- Clone sạch và ba lệnh README đã chạy thành công trên Windows, macOS và Linux (theo báo cáo của nhóm).

## Số liệu
Benchmark ba lần trên Windows, Chrome, 1280×720, seed 42: trung bình 59–60 FPS, 1% low 24–59 FPS (lần đầu có một đợt khung chậm). Xem `docs/proof/phase-4/`.

## Test
189 test, OK, trên commit phát hành (tag `phase-4`). Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.

## Ghi công
Không dùng tài sản hình hay âm thanh bên ngoài. Xem [CREDITS.md](CREDITS.md).

## Giấy phép
MIT. Xem [LICENSE](LICENSE).
