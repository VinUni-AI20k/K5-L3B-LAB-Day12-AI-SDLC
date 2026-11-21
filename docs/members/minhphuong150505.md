# minhphuong150505 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  + [2c8a197](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/2c8a197): Scenario validation cho customer fixtures, reserved và ràng buộc quán.
  + [fe96d5f](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fe96d5f): Khởi tạo customer fixture, tính kho khả dụng, suy ra reserved khi thiếu.
  + [e888a95](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/e888a95): Lịch khách đến tất định (phase_tick), chọn bàn trống nhỏ nhất.
  + [78e763f](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/78e763f): Chọn món ngẫu nhiên đều qua Streams, giữ chỗ nguyên liệu, phát customer_arrived và no_dish.
  + [0393768](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0393768): Đếm ngược kiên nhẫn, xử lý hết kiên nhẫn (customer_left), kẹp uy tín, giải phóng reserved.
  + [ada49d0](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/ada49d0): Bộ unit test và black-box test bao phủ AC-P1-07, AC-P1-08 và ca biên determinism.
- Tôi đã review (kèm link): Chưa review do chờ PR của phuthaitran (Lát 4).
- AI sai ở đâu và tôi phát hiện thế nào: AI dùng `c.get("reserved", {})` nhưng khi key `"reserved"` chứa giá trị `None` thì vẫn trả về `None`, gây `AttributeError` khi gọi `.items()`. Phát hiện khi chạy test `test_p1_lat3.py` và sửa thành `c.get("reserved") or {}`.
- Điều tôi học được: Quy trình test-driven kết hợp chia nhỏ commit giúp kiểm soát lỗi nhanh chóng; việc phân định ranh giới module rõ ràng giữa Lát 3 và Lát 4 giúp phát triển song song mà không xung đột.
