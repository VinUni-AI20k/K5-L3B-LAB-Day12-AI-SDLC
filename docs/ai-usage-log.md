# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | TV1 (Nguyễn Duy Mạnh) | Antigravity (Gemini 4 Hydrogen) | Triển khai sinh tồn ca sáng trong `chonoi/sim/gather.py`, viết 3 test headless `tests/test_gather_survival.py`, điền `docs/standup.md`, `docs/verification/phase-1.md` | Chưa đo | Tự đối chiếu thứ tự bước mục F và điều kiện biên `zero_oxy_ticks` (bước chạm oxy 0 tính là bước ngạt đầu tiên); chạy `tests/test_gather_survival.py` đạt 3/3. |
| 1 | TV2 | Antigravity (Gemini 4 Hydrogen) | Triển khai hái nút, bắt cá, cooldown, hòa ID trong `chonoi/sim/gather.py` và bộ test `tests/test_gather_harvest.py` | - | Tự động chạy kiểm chứng 9/9 test biên và smoke 2 tiến trình Mục G đều đạt. |
| 1 | TV4 | Codex | Đối chiếu mục D–F, triển khai bếp và thanh toán, viết và chạy test headless | Chưa đo | Xem [kết quả TV4](proof/phase-1/tv4-bep-thanh-toan.md). |
| Phase 1 | Vũ Xuân Bách (bachvx1709) | Gemini 3.8 Flash | Soạn thảo ma trận kiểm chứng `phase-1.md`, viết `test_phase1_gameplay.py`, tích hợp 3 tính năng sáng tạo Web Audio & Canvas UI | ~18.000 tokens | AI viết kịch bản test giữ nguyên phím `interact=True` khiến không phát hiện được cạnh lên ở thao tác tiếp theo; phát hiện khi chạy unittest fail và sửa nhả phím `interact=False` |
| Phase 1 | Hoàng Nam (hnamyud) | Gemini / Claude | Hỗ trợ code logic ca sáng `gather.py` (lặn, nổi, oxy, ngạt, ngất) | ~20.000 tokens | AI tính oxy theo vị trí đầu bước thay vì cuối bước; đối chiếu PRD mục F để kẹp oxy chuẩn theo d cuối bước |
| Phase 1 | Nguyễn Duy Mạnh (nguyenduymanh) | Gemini / Claude | Hỗ trợ code logic ca tối `quan.py` (bếp, khách, phục vụ, tính tiền, boa) | ~22.000 tokens | AI quên tính tiền boa khi khách được phục vụ với tỷ lệ kiên nhẫn >= 50%; đã sửa lại theo công thức `floor(base_price * tip_rate)` |
