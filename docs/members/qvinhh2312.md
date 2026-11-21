# qvinhh2312 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Phụ trách module `client/ui` (UX + Demo lead).
  - Hoàn thành HUD 2 buổi sáng/tối (Ticket 06) và độ tươi / hàng ươn contract v1.2 (Ticket 05 Phase 3).
  - Hoàn thành Ticket 03 Phase 4: 3 cảnh báo nguy hiểm chữ + icon (Thủy quái, Hết hơi, Khách giận) & Chế độ tương phản cao (phím `C`, `?hc=1`).
  - Sáng tạo âm thanh Web Audio API (0 KB asset) và hiệu ứng VFX bọt khí / khói bếp / cờ `?fx=0`.
  - Biên soạn kịch bản demo (`docs/demo.md`) và bằng chứng kiểm thử (`docs/proof/`).
- Tôi đã review:
  - Review chéo PR cho các thành viên trong nhóm theo quy ước luồng nhóm.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Ban đầu AI đề xuất dùng `alert()` và nạp MP3 ngoài làm đứng loop canvas và nặng repo; tôi đã kịp thời chuyển sang canvas overlay và Web Audio procedural 100% bằng mã.
- Điều tôi học được:
  - Nắm vững kiến trúc client null-safe, tối ưu hiệu năng và giữ vững tính tất định của headless contract.
