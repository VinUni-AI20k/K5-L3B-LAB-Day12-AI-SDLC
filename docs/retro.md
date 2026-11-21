# Retro nhóm Banana

## Phase 2 (nhanh)
- Điều tốt: Chia tách lát cắt rõ ràng (Lát 1-4, Shop, HUD); các thành viên push nhánh độc lập và tạo PR có kiểm tra kỹ.
- Điều tệ: Chưa có CI tự động nên việc kiểm tra hồi quy phải chạy thủ công cục bộ trước khi merge.
- 1 hành động cho Phase 3: Rà soát kỹ breaking change của kho cá thể v1.2 trước khi merge để tránh xung đột mã nguồn.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: Đã thực hiện nghiêm túc; các thành viên phối hợp rà soát schema v1.2 từ sớm nên khi tích hợp kho cá thể và độ tươi vào main không xảy ra xung đột lớn.
- Điều tốt / điều tệ:
  - Điều tốt: 100% thành viên đều có trên 3 commit chất lượng; hệ thống kiểm thử toàn diện đạt 141/141 test xanh; hoàn thành xuất sắc 2 mở rộng (Cháy món `burn` và Thiết lập âm thanh `settings/audio`); các pha đều hoàn thành và nộp đúng hạn.
  - Điều tệ: Đôi lúc việc review PR giữa các thành viên còn dồn vào cuối phase tạo nút thắt cổ chai nhỏ.
- Số liệu:
  - Số commit theo người: TV1 (Sang) ≥ 5, TV2 (Quỳnh Anh) ≥ 4, TV3 (Vinh) ≥ 5, TV4 (Quân) = 15 commit, TV5 (Cường) ≥ 4, TV6 (Quyên) ≥ 6.
  - Cách đọc code của nhau: Review chéo theo cặp chỉ định trong TEAM.md (TV1 ↔ TV2, TV3 ↔ TV4, TV5 ↔ TV6).
  - Token ước tính: TV4 dùng ~68,000 tokens qua Gemini / Antigravity.
- Rà soát tài nguyên & bản quyền: Đã đối chiếu CREDITS.md (toàn bộ đồ họa Canvas 2D và âm thanh Web Audio API đều tự lập trình, không dùng tài sản ngoài có bản quyền) và xác nhận giấy phép của dự án.
- Một lần AI sai và cách nhóm phát hiện:
  - AI tính giá chốt theo độ tươi lúc đầu tick mà bỏ qua hao tươi xảy ra trước bước tương tác nấu trong tick (lệch 1 đơn vị giá); TV4 phát hiện qua unit test và điều chỉnh lại thứ tự toán học chính xác theo PRD.
- Nếu làm lại, đổi gì:
  - Thiết lập GitHub Actions tự động chạy toàn bộ test suite khi mở PR để phát hiện hồi quy sớm hơn nữa.
