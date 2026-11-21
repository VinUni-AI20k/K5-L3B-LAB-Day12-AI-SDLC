# Đo FPS client (TV5)

| Lần đo | Điều kiện | Kết quả |
|---|---|---|
| 1 | Bộ ghép tạm (trước PR #11), ca sáng D1, 8 đàn cá đứng yên | 60.0 FPS TB, khung chậm nhất 17.7 ms |
| 2 (**bàn giao**) | DaySim thật sau PR #11: 10 đàn cá bơi + Cá Sấu M1, Út Sen lặn về phía quái | **60.0 FPS TB**, khung chậm nhất 17.7 ms, 300 khung |

- Cách chạy: `python3 -m chonoi.live --mode day`, mở `http://127.0.0.1:8000/?fps=1` (hoặc bấm **F3**), viewport giả lập **1280×720** (devicePixelRatio 2) trong Browser pane của Claude desktop (Chromium), macOS Darwin 25.5.
- Cách đo: `window.__perf.samples` (độ dài từng khung `requestAnimationFrame`), 300 khung liên tiếp.
- Ngưỡng: ≥ 30 FPS → **Đạt**.
- Lưu ý trung thực: Browser pane có lúc ở chế độ ẩn khi đo; rAF vẫn đủ 60 Hz. Nên bấm F3 đo lại trên máy demo.
- Ảnh: [ui/16-hud-gather-real-daysim-fps.jpg](ui/16-hud-gather-real-daysim-fps.jpg) (ảnh thu nhỏ 800×450 từ viewport 1280×720, góc trái dưới hiện "60 FPS · 1280×720").
