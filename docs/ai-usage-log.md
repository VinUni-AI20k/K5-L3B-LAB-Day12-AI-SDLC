# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | huydn8816 | Claude Code (Sonnet 5.5) | Chia việc 4 người; viết test luật `gather` và `quan` (`tests/test_rules_*.py`); bổ sung HUD buổi tối | Không đo được | Viết test trước khi đọc PRD-0 (không có trong repo) nên phải đoán luật (giỏ LIFO, bắt cá một phần, tick ngạt); sau khi có PRD-0 phải sửa lại nhiều test. Ban đầu AI chưa nối "Phase 1" với "PRD-0" và gợi ý lệnh `unittest` chạy sai chỗ |
| 2 | huydn8816 | Claude Code (Sonnet 5.5) | Test hợp đồng v1.1 và luật Phase 2 (`test_p2_*.py`, tự bỏ qua khi contract còn 1.0); viết lại `index.html` (menu, pause, HUD, Shop); smoke tích hợp và bằng chứng | Không đo được | AI không kiểm được giao diện bằng mắt cho tới khi chụp bằng Chrome: ảnh đầu cho thấy chữ đè nhau ở quán và "Thủy quái!" khó đọc trên nền sáng, phải sửa. Máy không có `python3` thật (chỉ stub Store) nên phải dựng bản `python3.exe` tạm để chạy test |
