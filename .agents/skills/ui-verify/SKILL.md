---
name: ui-verify
description: Quy trình kiểm tra toàn diện giao diện người dùng trực tiếp (Live UI/HUD), hệ thống âm thanh Web Audio và cờ tối ưu hóa đồ họa ?fx=0.
---

# Skill: ui-verify

Sử dụng skill này để xác thực các tính năng phía client web (`chonoi/web/index.html`) trước khi mở PR hoặc gắn tag release.

## 1. Khởi chạy chế độ chơi trực tiếp

```bash
# Khởi chạy buổi sáng (Gather: Lặn & Hái)
python3 -m chonoi.live --mode gather

# Khởi chạy buổi tối (Quán: Nấu & Phục vụ)
python3 -m chonoi.live --mode quan
```

Mở trình duyệt tại địa chỉ được in ra (thường là `http://127.0.0.1:<port>`).

## 2. Checklist kiểm tra nhanh bằng mắt & tai (60 giây)

- [ ] **Đồng hồ & Thanh trạng thái:** Đồng hồ đếm ngược `mm:ss` (chuyển đỏ khi < 30s), thanh Oxy đổi màu mượt mà (Xanh $\rightarrow$ Cam $\rightarrow$ Đỏ khi < 25%), Máu hiển thị tim ♥♥♥.
- [ ] **Prompt ngữ cảnh:**
  - Đi gần bến tàu: Hiện `[E] Cập bến`.
  - Mặt nước gần nút rau: Hiện `[E] Hái <tên loài>` (hoặc cảnh báo giỏ đầy).
  - Dưới nước gần đàn cá: Hiện `[Space] Bắt cá` (hoặc cảnh báo hồi chiêu).
- [ ] **Độ tươi & Hàng ươn (Phase 3 v1.2):**
  - Giỏ hàng hiện thanh độ tươi mini dưới đáy ô.
  - Cá thể có `fresh < 30` bị gạch chéo đỏ và hiện chữ `ƯƠN`.
  - Có banner toast hiện thông báo khi cá thể bị ươn (`spoiled`).
- [ ] **Hệ thống âm thanh Web Audio:**
  - Bấm phím `M` hoặc click nút `🔊 / 🔇` ở góc trên để bật/tắt âm thanh.
  - Nghe rõ tiếng lặn nước, thu hoạch, bắt cá, chuông bếp, tiếng trả tiền leng keng.
- [ ] **Tối ưu hóa máy yếu (`?fx=0`):**
  - Mở với `?fx=0` trên URL (`http://127.0.0.1:<port>/?fx=0`).
  - Kiểm tra các hạt bọt khí và khói bếp đã được tắt hoàn toàn để giảm tải CPU/GPU.
- [ ] **Màn kết thúc:** Hết giờ hoặc cập bến, màn Game Over hiển thị rõ ràng lý do, điểm số; click chuột vào nút `[Chơi lại]` hoặc phím `R` hoạt động mượt mà.
