# Retro nhóm MMMMV

## Phase 2 (nhanh)
- **Điều tốt:**
  - Nhóm phân chia vùng file độc lập xuất sắc, không ai giẫm chân lên code của nhau.
  - Client giao diện web được trang bị hệ thống âm thanh procedural Web Audio và hạt VFX mà không cần tải thêm bất kỳ file ngoài nào (0 KB asset), đảm bảo repo nhẹ và an toàn bản quyền.
- **Điều tệ:**
  - Kênh liên lạc về các quyết định schema đôi lúc bị lệch vài phút giữa PO và nhóm làm simulation.
- **1 hành động cho Phase 3:**
  - Khi PO công bố change request "Mùa Nước Nổi" (v1.2 kho cá thể và độ tươi), module UI (Vinh) sẽ cài đặt ngay khả năng nhận diện cả hai schema để kiểm thử không bị gián đoạn; bổ sung cờ `?fx=0` để tắt hiệu ứng trên máy yếu.

---

## Phase 4 (cuối)
- **Rà lại hành động Phase 2: đã làm chưa? vì sao?**
  - Đã làm hoàn tất: Ticket 05 (HUD độ tươi và hàng ươn) đã được hoàn thành ngay tại đầu Phase 3, tương thích ngược 100% với cả v1.0/v1.1 lẫn v1.2; cờ `?fx=0` đã được tích hợp thành công.
- **Điều tốt / điều tệ:**
  - *Điều tốt:* Tinh thần làm việc nhóm kỷ luật, tuân thủ nghiêm ngặt quy ước nhánh `feat/<tên>` và luồng review vòng tròn; simulation giữ vững tính tất định 100%; giao diện trực quan, sinh động có âm thanh và hiệu ứng hạt.
  - *Điều tệ:* Một vài bài unit test ban đầu phụ thuộc vào môi trường Windows stub khiến test chạy chậm, đã khắc phục bằng cách chuẩn hóa qua headless runner.
- **Số liệu thống kê:**
  - *Số commit theo người:* Mỗi thành viên đều đạt từ 4 đến 7 commits có nội dung thực tế (vượt mốc tối thiểu $\ge 3$ commits/người của rubric).
  - *Cách đọc code của nhau:* Review chéo nghiêm túc theo vòng tròn (Cao Minh $\rightarrow$ Đức Minh $\rightarrow$ Văn Minh $\rightarrow$ Vinh $\rightarrow$ Nhật Minh $\rightarrow$ Cao Minh).
  - *Token theo người:* Vinh sử dụng ~37.000 tokens (Gemini 3.8 Flash High) phục vụ code HUD canvas, thuật toán dao động Web Audio, tài liệu ma trận truy vết và kịch bản demo.
- **Một lần AI sai và cách nhóm phát hiện:**
  - *Lần AI sai:* Khi xây dựng tính năng thông báo và âm thanh ở Phase 1 & 2, AI ban đầu đề xuất dùng hàm `alert()` và nạp các tệp âm thanh `.wav` nặng vào repo.
  - *Cách phát hiện:* Vinh chạy thử trực tiếp trên trình duyệt, phát hiện ngay `alert()` làm dừng vòng lặp `requestAnimationFrame` của Canvas khiến game bị đơ cứng, đồng thời việc nạp tệp âm thanh ngoài vi phạm quy định hạn chế asset nặng. Vinh đã yêu cầu AI đổi sang in-canvas toast banner và tổng hợp âm thanh bằng Web Audio API thuần mã code.
- **Nếu làm lại, đổi gì:**
  - Sẽ thiết lập sẵn ma trận truy vết và test contract tự động ngay từ phút thứ 0 để giảm bớt thời gian chờ đợi giữa các nhịp chuyển giao schema.
