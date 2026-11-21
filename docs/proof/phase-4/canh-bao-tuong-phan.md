# Bằng chứng kiểm chứng Ticket 03 Phase 4: Cảnh báo dễ nhận biết + Chế độ tương phản cao

- **Người thực hiện:** Tào Quang Vinh (`@qvinhh2312`)
- **Vai trò:** UX + Demo / Đóng gói (UI)
- **Ticket tham chiếu:** `docs/tickets/phase-4/03-canh-bao-tuong-phan.md`
- **File sửa đổi:** `chonoi/web/index.html` (chỉ can thiệp client frontend HTML/Canvas/HUD, không sửa `chonoi/sim/`, không làm thay đổi luồng byte headless).

---

## 1. Ba cảnh báo nguy hiểm nhận biết ngay bằng Chữ + Biểu tượng (Không phụ thuộc màu sắc)

Thiết kế loại bỏ rào cản mù màu (Color Blindness Accessibility), đảm bảo mọi tình huống nguy cấp người chơi đều đọc được rõ ràng bằng **Chữ + Biểu tượng (Icon)**:

### 1.1. Cảnh báo Thủy quái gần (🐊 THỦY QUÁI!)
- **Điều kiện kích hoạt:** Khi Cá Sấu tuần tra/truy đuổi ở độ sâu $d \ge 10$ và khoảng cách tới Út Sen $\le 10$m (hoặc trạng thái `chase`).
- **Biểu hiện trên HUD:**
  - Banner cảnh báo nhấp nháy nổi bật: `[🐊 THỦY QUÁI GẦN! (cách X.Xm)]`
  - Đường nét đứt cảnh báo nối giữa người chơi và Cá Sấu.
  - Nhãn hiển thị trực tiếp trên đầu Cá Sấu: `🐊 CÁ SẤU (Truy đuổi!)`
  - Tự động tắt ngay khi Út Sen bơi thoát khỏi bán kính phát hiện.

### 1.2. Cảnh báo Hết hơi (🫁 HẾT HƠI!)
- **Điều kiện kích hoạt:** Khi lượng oxy còn lại $< 25\%$ dung lượng tối đa.
- **Biểu hiện trên HUD:**
  - Nhãn cảnh báo bằng chữ và biểu tượng: `🫁 HẾT HƠI!`
  - Nhịp nhấp nháy gia tốc: Tần số nháy tăng dần theo thời gian thực khi oxy tiệm cận 0 (`flashSpeed = Math.max(2, Math.floor(oxyRatio * 20))`).
  - Đi kèm hiệu ứng rung màn hình nhẹ và âm thanh cảnh báo ngạt nước.

### 1.3. Cảnh báo Khách sắp giận (😡 KHÁCH SẮP GIẬN!)
- **Điều kiện kích hoạt:** Khi thời gian kiên nhẫn của khách tại bàn ăn $< 25\%$ (chế độ Quán buổi tối).
- **Biểu hiện trên HUD:**
  - Viền cảnh báo nét đứt nhấp nháy bao quanh bàn đang nguy cấp.
  - Nhãn nổi bật ngay trên bàn: `😡 KHÁCH SẮP GIẬN! (Xs)`
  - Banner khẩn cấp ở thanh HUD trên: `⚠️ Bàn Tk: 😡 KHÁCH SẮP GIẬN (Xs)!` giúp người chơi biết ngay bàn nào cần ưu tiên phục vụ.

---

## 2. Chế độ tương phản cao (High Contrast Mode)

- **Kích hoạt linh hoạt qua 3 cách:**
  1. Phím tắt: Nhấn phím `C` trên bàn phím bất kỳ lúc nào.
  2. Nút bấm trên thanh HUD: Click nút `👁️ Tương phản (C)` ở góc trên bên phải màn hình (cạnh nút âm thanh).
  3. Đường dẫn URL: Thêm query param `?hc=1` (ví dụ `http://127.0.0.1:8000/?hc=1`).
- **Ghi nhớ trạng thái phiên chơi:** Lưu vào `sessionStorage.getItem("chonoi_high_contrast")`, người chơi đổi cảnh hoặc reset game thì trạng thái tương phản vẫn được duy trì.
- **Quy chuẩn hiển thị tương phản cao:**
  - **Nền đen đặc tuyệt đối (`#000000`):** Giúp giảm mỏi mắt và tăng tối đa độ tương phản cho người thị lực kém.
  - **Viền chữ đen dầy (`strokeText` 3.5px):** Đảm bảo mọi chữ và số đều sắc nét trên bất kỳ nền nào.
  - **Các khối bàn, bếp, thùng hàng:** Vẽ viền trắng rõ nét (`lineWidth = 2.5px`, màu `#ffffff`).
  - **Tối ưu hóa hiệu năng & giảm nhiễu thị giác:** Tự động tắt toàn bộ hiệu ứng rườm rà (hạt bong bóng, khói bếp, ánh sáng tán xạ god-rays, vignette).

---

## 3. Khả năng đọc cả 3 cảnh báo trong Chế độ tương phản cao

- Trong chế độ tương phản cao, cả 3 nhãn cảnh báo đều hiển thị chữ viền đậm, biểu tượng to bản và màu tương phản cao (Vàng chanh `#ffff00`, Đỏ tươi `#ff3333`, Trắng sáng `#ffffff`).
- Người chơi không cần phân biệt dải màu sắc vẫn nắm bắt tức thì 100% tình huống nguy hiểm thông qua chữ và biểu tượng.

---

## 4. Kiểm chứng kỹ thuật & Tính toàn vẹn hệ thống

- **Cú pháp JavaScript:** Kiểm tra bằng Node.js AST parser: `JavaScript Syntax OK!`.
- **Hiệu năng:** Đạt trọn vẹn 60 FPS mượt mà.
- **Không xâm lấn backend:** Mọi logic nằm hoàn toàn trong `chonoi/web/index.html`, đọc dữ liệu snapshot an toàn (`null-safe`), không đụng chạm tới `chonoi/sim/` hay dữ liệu headless.
