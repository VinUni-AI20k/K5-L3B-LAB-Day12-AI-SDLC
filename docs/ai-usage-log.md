# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Vũ Xuân Bách (bachvx1709) | Gemini 3.8 Flash | Soạn thảo ma trận kiểm chứng `phase-1.md`, viết `test_phase1_gameplay.py`, tích hợp 3 tính năng sáng tạo Web Audio & Canvas UI | ~18.000 tokens | AI viết kịch bản test giữ nguyên phím `interact=True` khiến không phát hiện được cạnh lên ở thao tác tiếp theo; phát hiện khi chạy unittest fail và sửa nhả phím `interact=False` |
| Phase 1 | Hoàng Nam (hnamyud) | Gemini / Claude | Hỗ trợ code logic ca sáng `gather.py` (lặn, nổi, oxy, ngạt, ngất) | ~20.000 tokens | AI tính oxy theo vị trí đầu bước thay vì cuối bước; đối chiếu PRD mục F để kẹp oxy chuẩn theo d cuối bước |
| Phase 1 | Nguyễn Duy Mạnh (nguyenduymanh) | Gemini / Claude | Hỗ trợ code logic ca tối `quan.py` (bếp, khách, phục vụ, tính tiền, boa) | ~22.000 tokens | AI quên tính tiền boa khi khách được phục vụ với tỷ lệ kiên nhẫn >= 50%; đã sửa lại theo công thức `floor(base_price * tip_rate)` |
