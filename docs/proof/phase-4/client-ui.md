# Bằng chứng UI TICKET-04

Nền tích hợp `527645f` của nhánh `hung`. Checkout đang dùng Test Contract v1.1. Benchmark dưới đây đo Gather thật của checkout, gồm cá, cá sấu và hiệu ứng Canvas. Phép đo chính thức với sim độ tươi cần chạy lại khi bản v1.2 được tích hợp.

## Benchmark render

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
```

Entrypoint lấy mốc `perf_counter()` ngay khi nạp module. Nó chạy máy chủ live ở loopback với sim 60 Hz và khởi động Chromium ở 1280×720. Út Sen đứng yên ở bến. Trình duyệt báo mỗi khung Canvas đã vẽ từ nhịp vẽ tiếp theo, sau khi Chromium có cơ hội trình chiếu khung trước. Tiến trình Python đo thời điểm nhận tín hiệu bằng `perf_counter()`.

`load_ms` tính đến tín hiệu khung đầu tiên. Loại 3 giây làm nóng và chỉ lấy các khoảng giữa hai khung nằm trong cửa sổ đo. FPS trung bình dùng `avg_fps = frames / sum(dt)`. Giá trị `p1_low_fps = 1 / p99(dt)` dùng hạng gần nhất. `measured_s` là tổng thời gian các khoảng được lấy. Lệnh ghi đúng năm trường JSON và đóng Chromium cùng máy chủ thử nghiệm.

| Seed | Thời gian yêu cầu | FPS trung bình | p1 low FPS | Khung đo | Thời gian đo | Tải cảnh |
|---|---|---|---|---|---|---|
| 42 | 30 s | 143,94 | 126,79 | 4317 | 29,992 s | 908 ms |

[bench.json](bench.json) được tạo khi chạy đúng `bench_cmd` từ bản xuất sạch trên Windows với Chrome. Chrome hoặc Chromium phải có sẵn trên máy chạy. Entrypoint tìm qua `PATH`, vị trí cài phổ biến hoặc `CHONOI_BROWSER`.

## Cảnh báo và tương phản

- Chrome kiểm ở 1280×720, chữ không chân từ 18 px. Oxy dưới 25%, thủy quái gần hoặc đuổi và khách có kiên nhẫn dưới 25% đều hiện chữ và biểu tượng.
- Kiểm nút tương phản ở menu và Pause, lưu qua tải lại, cập nhật cả nền Canvas. Các cảnh Gather/Quán, đường live v1.1 và bản xem Phase 1–3 đều mở được. Chi tiết công thức và giá trong thực đơn kho đếm có thể mở từng món.
- Suite trên bản xuất sạch đạt 54/57, cùng ba lỗi headless đã có trên nền. Smoke bàn giao kho đạt 1/1. JSONL Gather và Quán seed 42, 600 tick giống từng byte với nền.
