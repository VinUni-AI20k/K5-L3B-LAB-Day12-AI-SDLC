# Kiểm chứng nội dung mở rộng

- Suite `python -m unittest discover -s tests` đạt 32/32. Khi chạy trên Windows, trong tiến trình test dùng `sys.executable` thay cho alias `python3` của lệnh headless để tránh WinError 1920.
- Gọi `chonoi.live.main` với `--extra-content` cho cả `gather` và `quan`, dùng máy chủ giả lập để kiểm tra cấu hình. Cả hai chế độ nạp thêm hai loài cá, hai loại rau và ba công thức. Mỗi nguyên liệu mới xuất hiện trong ít nhất một công thức.
