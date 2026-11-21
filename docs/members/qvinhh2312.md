# qvinhh2312 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Phụ trách module `client/ui` (UX + Demo lead).
  - Hoàn thành HUD 2 buổi sáng/tối (Ticket 06) và nâng cấp hiển thị độ tươi / hàng ươn theo contract v1.2 (Ticket 05 Phase 3).
  - Tích hợp banner nhắc phím ngữ cảnh (Bến, Nút, Cá, Bếp, Bàn) và toast cảnh báo cá thể ươn `spoiled`.
  - Sáng tạo hệ thống âm thanh tự sinh Web Audio API (0 KB asset ngoài) và hiệu ứng VFX hạt bọt khí / khói bếp / cờ `?fx=0`.
  - Biên soạn kịch bản demo 3 phút (`docs/demo.md`) và đầy đủ tài liệu kiểm chứng (`docs/proof/`).
- Tôi đã review (kèm link):
  - Chuẩn bị review cho PR của Nguyễn Văn Minh (`feat/van-minh`) theo quy ước luồng nhóm.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Ban đầu AI đề xuất dùng `alert()` và nạp file MP3 ngoài làm đứng loop canvas và tăng kích thước repo; tôi đã kịp thời chuyển sang canvas overlay và bộ tạo dao động âm thanh Web Audio hoàn toàn bằng mã.
- Điều tôi học được:
  - Nắm vững kiến trúc client null-safe tương thích cả 2 chuẩn schema kho (đếm v1.0 và cá thể v1.2), tối ưu hiệu năng đồ họa và giữ vững tính tất định của headless contract.
