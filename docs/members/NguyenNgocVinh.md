# NguyenNgocVinh — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm** — Phụ trách TV3 (Khách + PO). Tôi triển khai khách đến theo lịch, chọn món đủ nguyên liệu, giữ phần cho đơn và xử lý khi khách rời. Tôi đối chiếu PRD-0 mục F, cập nhật `docs/clarify.md` và ghép luồng khách với bếp, phục vụ và thanh toán. [Commit TV3](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/1f10afe56d4c2c6e10882296ac3b091ab5e47bec) · [Commit tích hợp TV4](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/4f1b3c0ac8206e83d6c26aaf5f5e316bc4ac9b3a)
- **Tôi đã review** — Rà luồng bàn giao kho của TV2, chạy lại lượt thu mẫu và xác nhận kho xuất khớp tồn kho quán ở tick 0. [Công cụ kiểm kho](../../tools/check_handoff.py) · [Bằng chứng](../proof/phase-1/handoff.txt)
- **AI sai ở đâu và tôi phát hiện thế nào** — Bản đầu xử lý khách bỏ đi trước lượt tương tác. Khi đối chiếu mục F, tôi thấy khách vẫn có thể nhận món đúng tick kiên nhẫn về 0, nên chuyển xử lý khách rời xuống sau lượt tương tác.
- **Điều tôi học được** — Có thể dùng kho mẫu để phát triển độc lập. Khi ghép phần khách với bếp, thứ tự xử lý trong một tick quyết định kết quả ở các ca biên.
