# BLong1501 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - Lát 2 `chonoi/sim/gather.py` (`AC-P1-20..23`): hái nút ở mặt nước, bắt cá dưới nước, `hold_full`, hồi chiêu, hành động ở tick cuối (`20cc53d`).
  - Viết 16 test hộp đen trong `tests/test_gather_slice2.py`; chạy đạt 48/48 unittest, 12/12 kiểm tất định, 10/10 smoke hai tiến trình.
  - Cập nhật HUD `chonoi/web/index.html` (`AC-P1-53`): tính và hiển thị kho khả dụng (`stock - reserved`), trạng thái bếp/khách, món trên tay, sửa lỗi hiển thị object `st.dish`.
  - Cập nhật `docs/standup.md`, `docs/ai-usage-log.md`.
- **Tôi đã review:** (Sẽ bổ sung link PR sau khi review chéo Lát 1 của `LyLe10`.)
- **AI sai ở đâu và tôi phát hiện thế nào:** AI đưa lệnh kiểu Linux/Bash (`PYTHONPATH=tests:.`) không chạy được trên PowerShell và không tìm thấy Python trong môi trường chạy lệnh; tôi tự chạy kiểm chứng trực tiếp trên PowerShell và kiểm tra giao diện qua `chonoi.live`.
- **Điều tôi học được:** Tách nhánh theo lát và đọc kỹ hợp đồng (`docs/contracts/README.md`) trước khi code giúp ghép phần mình vào khung chung nhanh và ít xung đột; luôn tự chạy lại test + skill kiểm tra thay vì tin hoàn toàn vào output giả định.
