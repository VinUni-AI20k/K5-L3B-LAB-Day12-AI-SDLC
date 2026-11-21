> Sau merge: manifest v1.1 và Q3/Q4 đã có trên main; DaySim và phê duyệt hợp đồng còn mở. Xem [research](research.md), [handoff](handoff.md). Nội dung dưới là baseline lịch sử.

# Phase 2 Q3 — khách và kế hoạch ngày

Nguồn: `docs/plan/phase-2.md`, `docs/plan/phan-chia-cong-viec.md` và yêu cầu người dùng. Ticket-02 gốc và Test Contract v1.1 chưa truy cập được; kế hoạch nhóm là nguồn thứ cấp.

- US1: khách đến theo first tick và interval từ tuning, bàn trống có ID nhỏ nhất; không có bàn hoặc món nấu được thì bỏ cơ hội, không xếp hàng (chính sách tạm thời).
- US2: Quán độc lập xét toàn menu; Day truyền `menu_filter`; xét filter trước nguyên liệu, sort ổn định và chọn bằng Streams, giữ cả recipe nguyên khối.
- US3: giữ và tiêu thụ đúng một lần, nhả khi khách rời; bàn giải phóng khi rời hoặc thanh toán. Khách mới có `order_tick` là tick đến, fixture mặc định 0.
- US4: cung cấp snapshot khách và interface Q4/Day; không tự chốt no_dish, penalty order hay chính sách món mồ côi.

AC nội bộ: bốn bàn không trùng; lịch 120/1020/1920 với tuning thử; sáu món thử được chọn khi đủ nguyên liệu; filter rỗng không sinh; cùng seed tái lập; reservation không vượt kho. Chưa ánh xạ AC chính thức.
