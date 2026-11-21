# Bằng Chứng Kiểm Chứng HUD Độ Tươi & Hàng Ươn (Ticket 05 — Phase 3)

> **Người thực hiện:** Tào Quang Vinh (`@qvinhh2312` — UX + Demo lead)  
> **Module:** `client/ui` (`chonoi/web/index.html`)  
> **Ticket:** `docs/tickets/phase-3/05-hud-do-tuoi.md`

---

## 1. Ma trận tiêu chí chấp nhận (Acceptance Criteria)

| Tiêu chí trong Ticket 05 | Hiện thực trong `chonoi/web/index.html` | Kết quả |
|---|---|:---:|
| **Giỏ buổi sáng có độ tươi & hàng ươn:** | Mỗi slot trong giỏ kiểm tra thuộc tính `fresh`. Nếu `fresh < 30`, vẽ gạch chéo đỏ `#ff1744` và nhãn `ƯƠN`. Nếu `fresh >= 30`, vẽ thanh mini dưới đáy ô với màu xanh ($\ge 70$) hoặc vàng ($30-70$). | **ĐẠT** |
| **Kho quán có độ tươi:** | Phân loại `stock` mảng cá thể: thống kê hàng tươi khả dụng, lọc riêng các cá thể ươn và đánh dấu `⚠️ hàng ươn (không thể dùng)`. | **ĐẠT** |
| **Thông báo sự kiện `spoiled`:** | Khi nhận event `spoiled`, kích hoạt âm thanh cảnh báo `playAlert()` và hiển thị banner toast tự mờ dần sau 3 giây. Dùng `Set` ghi nhớ id cá thể để **không spam** khi độ tươi tiếp tục giảm. | **ĐẠT** |
| **Hỗ trợ `?fx=0`:** | Đọc URL query parameter `fx=0`. Khi bật, tắt toàn bộ hệ thống hạt (bọt khí, khói bếp) và giải thuật biến dạng sóng nước, giúp chạy siêu nhẹ trên máy yếu. | **ĐẠT** |
| **Tương thích ngược (v1.0 / v1.1):** | Khi chạy với dữ liệu không có trường `fresh` (mảng string), HUD tự động ẩn thanh độ tươi, giữ nguyên giao diện chuẩn, hoàn toàn `null-safe`. | **ĐẠT** |
| **Bảo toàn Headless:** | 100% mã nằm trong `chonoi/web/index.html`, không can thiệp Python simulation backend, headless output giống từng byte. | **ĐẠT** |

---

## 2. Lệnh kiểm chứng
```bash
# Kiểm thử giao diện có tham số tắt hiệu ứng nặng
python3 -m chonoi.live --mode gather
# Truy cập: http://127.0.0.1:<port>/?fx=0

# Kiểm thử headless invariance
python3 -m chonoi.headless --mode gather --seed 42 --ticks 180 --out out_p3_test.jsonl
```
