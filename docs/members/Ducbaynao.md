# Ducbaynao — phản tư cá nhân

Tôi là Phạm Lý Ngọc Đức, phụ trách Gather Core ở Phase 1.

- Tôi đã làm: [chuyển vùng và oxy](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/9b884d2), [ngạt và ngất](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/1fb7fbe), cùng giỏ LIFO, snapshot và [hồ sơ kiểm chứng](../proof/phase-1/member-2/README.md). Các liên kết commit có hiệu lực trên GitHub sau khi đẩy nhánh.
- Tôi đã đối chiếu [hợp đồng tích hợp](../contracts/README.md), thứ tự cập nhật trong [runner](../../chonoi/runner.py) và ba commit của lượt trước. Tôi chưa thực hiện review phần triển khai của thành viên 3.
- AI gặp vướng mắc khi dùng lệnh kiểm thử kiểu Linux trên Windows: alias `python3` không chạy được và mã hóa mặc định gây lỗi đọc stderr. Tôi xử lý bằng launcher tạm và UTF-8, không sửa contract để né lỗi.
- Tôi học được rằng thứ tự cập nhật trong một tick quyết định kết quả: oxy tính sau di chuyển, còn ngất phải xử lý trước cập bến và hết giờ. Tôi bổ sung test biên và lưu log thật; 45 test đều qua. Hồ sơ nhóm vẫn thiếu thông tin thành viên 3–6.
