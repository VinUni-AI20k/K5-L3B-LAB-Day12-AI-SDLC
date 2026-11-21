# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Vũ Quang Thanh (`thanhvu101`) | Antigravity (Gemini) | `M5.1`: Cập nhật `AGENTS.md`, tạo 2 skill (`verify-phase`, `ui-contract-sync`) trong `.agents/skills/` và khởi tạo `docs/ai-usage-log.md` | ~12k tokens | Cần nhắc AI không tự ý sửa `docs/contracts/` đã khóa bởi M6 mà tách tài liệu UI sang `docs/ui-contract.md`. |
| Phase 1 | Vũ Quang Thanh (`thanhvu101`) | Antigravity (Gemini) | `M5.2`: Lập danh sách chi tiết các trường UI đọc từ `GET /state` và lệnh gửi qua `POST /input`, `POST /restart` tại `docs/ui-contract.md` | ~10k tokens | AI cần phân biệt rõ trục thứ 2 của `move`: ở `gather` đi xuống là `+d`, còn ở `quan` đi lên (hướng bắc) là `+z`. |
| Phase 1 | Vũ Quang Thanh (`thanhvu101`) | Antigravity (Gemini) | `M5.3`: Thiết kế HUD buổi sáng (`gather`) và quán ăn nhà bè (`quan`) trên `chonoi.live` (`chonoi/web/index.html`), hỗ trợ phục vụ `/assets/` trong `chonoi/live.py` với fallback vẽ Canvas 2D khi chưa thêm ảnh/nhạc | ~25k tokens | Ban đầu cần lưu ý tính đúng "Kho khả dụng" = `stock` vật lý trừ tổng `reserved` của các đơn khách đang giữ chỗ, và hiển thị ngưỡng 50% kiên nhẫn để nhận tiền boa. |
