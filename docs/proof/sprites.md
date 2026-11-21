# Kiểm chứng sprite Chợ Nổi

- Suite `python -m unittest discover -s tests` đạt 32/32. Trên Windows, dùng `sys.executable` thay alias `python3` trong tiến trình test khi gọi headless.
- Khởi động `LiveServer` ở cả `gather` và `quan`, tải HTML và atlas qua HTTP, kiểm tra MIME `image/png`, ảnh RGBA và 12 vùng sprite có cả pixel trong suốt lẫn pixel đục.
- Ảnh được kiểm tra trực quan qua bản xem trước ImageGen. Chưa kiểm tra canvas bằng trình duyệt.
- Animation bơi dùng `ut-sen-swim.png`. Đã tải PNG qua HTTP ở chế độ `gather` và kiểm tra sáu vùng RGBA có nền trong suốt. Suite chạy lại đạt 32/32.
