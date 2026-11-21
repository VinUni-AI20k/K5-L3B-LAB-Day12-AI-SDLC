# bomgoa1102 — phản tư cá nhân

Tôi phụ trách phần Gather: bơi, oxy, hái, bắt cá và bàn giao kho; sau đó bổ sung cá di chuyển, cá sấu và logic độ tươi. Bằng chứng có trong [kiểm chứng Phase 2](../proof/phase-2/gather.md), [kiểm chứng Phase 3](../proof/phase-3/gather.md) và commit `60f77df`. Tôi chuẩn bị các trường hợp biên để nhóm dùng khi kiểm tra tích hợp.

AI từng nhầm vai UI và QA khi đề xuất chia việc Phase 3. Đối chiếu lại bảng phân công trong `TEAM.md` cho thấy Duy Hưng phụ trách UI, còn Nhật Minh phụ trách QA. Lỗi này nhắc tôi phải kiểm tra nguồn trong repo trước khi dùng kết quả AI, nhất là khi thông tin nhóm đã thay đổi.

Tôi học được rằng test logic riêng đạt chưa đủ để kết luận tính năng hoàn thành: Gather còn phụ thuộc schema kho, runner và phần Quán. Cần kiểm tra lại luồng bàn giao trên bản tích hợp của nhóm.
