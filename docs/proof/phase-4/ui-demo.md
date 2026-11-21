# Kiểm tra giao diện demo Mùa Nước Nổi

Chạy từ gốc repo bằng `python3 -m chonoi.live --mode gather`. Trên Windows dùng `python`. **Bắt đầu hành trình** mở bản xem trước 5 ngày, có thể duyệt tình huống bằng phím **E** và **Space**. **Chơi trọn ngày** dùng sim hiện tại để thu hoạch và bàn giao kho sang quán.

## Kiểm tra trên Chrome

- Duyệt menu, đủ 5 ngày, bàn giao kho, quán, cửa hàng và tổng kết ở 1280 × 720. Các màn kiểm tra vừa khung và nhãn điều khiển, cảnh báo, thông tin chơi được kiểm có cỡ chữ từ 18 px.
- Kiểm tra ba cảnh báo có chữ và biểu tượng, bật tương phản từ màn tạm dừng, chuyển kho qua live adapter và mở các bản xem riêng của Phase 1–3.
- Ở khung rộng 390 px, menu giữ được nút vào hành trình và ba chế độ chơi trong chiều ngang màn hình.

## Benchmark render và hồi quy

Chạy benchmark 30 giây với seed 42 từ bản xuất sạch của checkout, dùng Chrome trên Windows và mô phỏng Gather của Test Contract v1.1.

| FPS trung bình | p1 low FPS | Khung đo | Thời gian đo | Tải cảnh |
| --- | --- | --- | --- | --- |
| 143,94 | 127,95 | 4317 | 29,992 s | 841 ms |

Suite Python đạt 54/57, cùng ba ca headless thất bại trên commit nền `78c6f67` (fixture `hold`, mua nâng cấp với `--days` và tạm dừng). Smoke test bàn giao kho đạt. JSONL của Gather và Quán ở seed 42, 600 tick trùng từng byte với commit nền.

## Ảnh bìa

Ảnh minh họa được tạo bằng công cụ ImageGen tích hợp và lưu tại [chonoi/web/river-cover.webp](../../../chonoi/web/river-cover.webp) (1800 × 720, khoảng 191 KiB). `chonoi/live.py` thêm ảnh vào danh sách tệp tĩnh được phục vụ để bản clone chạy ngay bằng lệnh live. Menu dùng cảnh Canvas sẵn có nếu ảnh chưa tải được.

**Prompt**

> Original widescreen 2.5:1 menu-cover illustration for the Vietnamese indie game Quán Ăn Chợ Nổi. Landscape edge-to-edge, no text, no logos, no border. A southern Vietnamese floating market in the Mekong Delta during flood season at first sunrise. On the right 55–88%, Út Sen faces away from the camera, a young Vietnamese woman wearing a faded brick-red áo bà ba, checked khăn rằn and a practical nón lá, standing in a narrow wooden sampan amidst small piles of water lilies and a wicker basket. She paddles toward boat vendors and stilt houses lit with warm lanterns, nipa palms, drifting floodwater and low mist. Put the main subject at x 71%, with the boat visible in the lower right and an amber sun above or behind her. Keep the left 45% quiet and very dark deep bottle-green, with low-detail shadowed water and palms for real HTML title and buttons. High-end hand-painted narrative game key art, layered gouache washes with subtle carved woodblock edges, expressive brush grain, warm honey, burnt persimmon, jungle green and blue-black shadows. Natural authentic river culture, moody cinematic lighting, distinct foreground/background depth, amber reflections, visually rich right half, clean and readable silhouette. No text of any kind, no graphic overlay, no copied characters or existing game assets.
