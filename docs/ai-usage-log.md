# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Đỗ Việt Anh | Gemini | Cài đặt logic Quán (Lát 3: đón khách, giữ chỗ; Lát 4: nấu, phục vụ, tính tiền, tip, uy tín) & viết unit test | ~15,000 tokens | AI cần lưu ý xử lý tick 3720 là mốc spawn khách mới (bội số 900 tick) ngay sau khi khách cũ rời bàn do hết kiên nhẫn. |
| Phase 1 | Trần Đức Trung | ChatGPT | Cài đặt logic Gather (Lát 1: oxy, máu, ngạt, ngất; Lát 2: hái nút, bắt cá, cập bến) & 15 unit tests | ~16,000 tokens | AI đặt nhầm tên trường payload là count thay vì amount trong gather và yield trong fish_caught. |
| Phase 1 | Vũ Thành | Gemini | Setup team, hợp đồng clarify, xây dựng 2 AI skills tự động hóa (verify-phase, inventory-validator) | ~12,000 tokens | AI ban đầu đề xuất lệnh python3 trên môi trường Windows gây lỗi 9009, cần bổ sung fallback đa nền tảng trong helpers.py. |