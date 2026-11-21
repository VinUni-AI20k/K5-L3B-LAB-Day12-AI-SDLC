# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | phong (TV1) | Copilot / Claude | Lập trình Lát 1 Gather (bơi, oxy, ngạt, ngất, giỏ LIFO), bổ sung test unit `test_gather_lat1.py` | ~25k tokens | AI đôi khi nhầm lẫn tọa độ trục $d$ hướng xuống với trục y chuẩn |
| Phase 1 | thangdktd (TV2) | GitHub Copilot | Triển khai Lát 2 Gather (hái rau, bắt cá, hồi chiêu, cập bến xuất kho) | ~20k tokens | Cần bổ sung prompt rõ về quy tắc hòa ID nhỏ hơn khi khoảng cách bằng nhau |
| Phase 1 | daohiep2903 (TV3) | Codex / Copilot | Triển khai Lát 3 Quán (khách đến theo chu kỳ, kiểm tra kho, đặt chỗ `reserved`, độ kiên nhẫn) | ~22k tokens | AI ban đầu trừ kho trực tiếp thay vì giữ chỗ trong `reserved` |
| Phase 1 | nguyentronglam (TV4) | Codex / Claude | Triển khai Lát 4 Quán (bếp nấu, bưng bê, phục vụ, tính tiền, boa, uy tín, script tự lái E2E) | ~30k tokens | AI giả định khách hết kiên nhẫn vẫn giữ món trên tay người chơi |
| Phase 1 | vuhieuvh (TV5) | Antigravity (Gemini 3.8 Flash) | Khởi tạo ma trận truy vết AC-P1, kiểm thử độc lập 4 lát cắt, xác thực tính tất định và handoff file kho | ~20k tokens | AI ban đầu chưa nhận diện được môi trường Windows thiếu binary python3, cần thêm shim |
| Phase 2 | phong (TV1) | Copilot / Claude | Triển khai Quái Cá Sấu M1/M2 (tuần tra, đuổi theo, cắn trừ máu, rớt đồ LIFO, recoil) | ~28k tokens | AI quên giới hạn độ sâu $d \ge 10$ khiến cá sấu đuổi người chơi lên mặt nước |
| Phase 2 | thangdktd (TV2) | GitHub Copilot | Triển khai Đàn cá bơi phản xạ biên, đổi hướng và spawn chu kỳ 360 tick | ~24k tokens | AI tính sai góc phản xạ khi cá chạm góc 2 biên |
| Phase 2 | daohiep2903 (TV3) | Codex / Copilot | Triển khai lọc thực đơn Quán theo kế hoạch ngày (`day_dishes`) | ~18k tokens | AI cần được nhắc lọc thực đơn trước khi thực hiện giữ chỗ nguyên liệu |
| Phase 2 | nguyentronglam (TV4) | Codex / Claude | Triển khai vòng đời `--mode day` (DayIntro, gather, quan, shop, pause) | ~35k tokens | AI ban đầu kích hoạt nâng cấp ngay trong ngày thay vì dời sang ngày tiếp theo |
| Phase 2 | vuhieuvh (TV5) | Antigravity (Gemini 3.8 Flash) | QA Lead, tích hợp 5 lát cắt, kiểm thử hồi quy 78/78 tests, thiết kế giải phẫu Cá Sấu Web | ~25k tokens | AI khai báo trùng biến `const p` trong canvas gây lỗi màn hình đen |
