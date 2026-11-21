# Ducbaynao — phản tư cá nhân

Tôi là Phạm Lý Ngọc Đức, phụ trách Gather Core ở Phase 1.

- Tôi triển khai [oxy/chuyển vùng](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/9b884d2), [ngạt/ngất](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/1fb7fbe), giỏ và snapshot. Tôi tiếp tục hiệu chỉnh trên nhánh `fix/ducbaynao-gather-prd-payloads`; [báo cáo](../proof/phase-1/member-2/README.md) ghi kết quả mới.
- Tôi đối chiếu PRD-0 E/F/G, hợp đồng nội bộ và đường hái/bắt cá của TV3. Tôi chưa review đầy đủ luật quán.
- AI đã dựa vào hợp đồng nội bộ sai, khiến `oxygen_empty` thiếu `oxygen_ticks`, `faint` thiếu `cause/lost/hp`. Test cũ còn xác nhận payload sai. Tôi sửa kỳ vọng theo PRD, xác nhận ba test thất bại trước khi sửa code, rồi bổ sung test CLI cho LIFO, giỏ rỗng và nguyên liệu trùng.
- Tôi học được rằng test xanh chưa đủ nếu nguồn kỳ vọng sai. Tôi cần đối chiếu PRD gốc và JSONL thực xuất. Sau sửa, 70 test đều qua, kho ngất rỗng và kết quả tất định. Hồ sơ nhóm còn thiếu thành viên 6.

## Phase 2

Tôi tích hợp cá bơi/sinh và Cá Sấu M1/M2 từ gói TV2; sửa validator và giữ phần Quán hiện hành. Tôi học được rằng gói bàn giao có thể dựa trên phiên bản nền khác: chép toàn file sẽ kéo theo thay đổi ngoài phạm vi. [Bàn giao và kết quả 78 test](../proof/phase-2/member-2/README.md) ghi rõ phạm vi đã kiểm chứng và phần ngày/shop chờ TV1.
