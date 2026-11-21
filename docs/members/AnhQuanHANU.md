# AnhQuanHANU — phản tư cá nhân (≤ 200 từ)

## Phase 1
- **Tôi đã làm (kèm link commit):**
  - Cài đặt toàn bộ Lát 4 của chế độ Mở Quán (`sim/quan`): logic Bếp nấu món, bưng bê, phục vụ tại bàn, tính tiền món và tiền boa (`tip`), cộng điểm uy tín (`reputation`), xử lý khách ăn xong hoặc thanh toán khi đóng ca.
  - Viết bộ unit test chuyên biệt `tests/test_tv4_quan.py` kiểm chứng toàn diện các sự kiện: `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `quan_end`.
  - Thiết kế kịch bản test mẫu `tests/scenarios/test_tv4_bep.json` để TV6 (QA) nghiệm thu độc lặp.

- **Tôi đã review (kèm link):**
  - Rà soát giao diện kết nối giữa Lát 3 (Khách) và Lát 4 (Bếp) với TV3, đảm bảo thứ tự ưu tiên interact và cấu trúc dữ liệu khách hàng khớp 100% PRD-0.

- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu tính mốc tick của sự kiện `dish_ready` là tick 360, nhưng theo hợp đồng PRD-0 mục F ("bước k biến trạng thái k thành k+1 và ghi event tại k+1"), tick của event phải là 361. Tôi đã phát hiện qua test runner và điều chỉnh lại kiểm thử cho khớp hoàn toàn quy ước event tick của giảng viên.

- **Điều tôi học được:**
  - Kỹ năng chia nhỏ lát cắt tính năng (slice-based development) để phát triển và kiểm thử độc lập mà không bị nghẽn (block) bởi các thành viên khác trong nhóm.

## Phase 2
- **Tôi đã làm:**
  - Cài đặt module `chonoi/sim/shop.py` (`ShopSim`): xử lý mua nâng cấp `oxygen` và `hp`, kiểm tra đủ tiền (`funds`), kẹp cấp tối đa (`max_level`), trừ tiền `money` mà không ảnh hưởng `earned` và điểm số, cập nhật `upgrades` ngay lập tức trong khi giữ nguyên `active_upgrades` cho ngày sau, cơ chế thoát shop qua nút `shop_done` hoặc timeout 600 tick.
  - Cài đặt mở rộng Cháy món (`burn`) trong `chonoi/sim/quan.py`: kiểm tra tuổi món `ready_ticks > burn_ticks` (1200 ticks với `burn_s: 20`), phát sự kiện `dish_burnt`, giải phóng bếp về `idle`, tự động kiểm tra tồn kho để giữ lại nguyên liệu (`reserved`) hoặc chuyển đơn sang `unfulfillable`.
  - Xây dựng bộ test `tests/test_tv4_phase2.py` bao phủ toàn diện các trường hợp mua hợp lệ, lỗi mua thiếu tiền, vượt cấp, lệnh lạ, thoát shop và kiểm chứng cháy món.
- **Tôi đã review:**
  - Rà soát hợp đồng giao diện `ShopSim` với TV1 (Sang) để tích hợp vào runner `--mode day`.
  - Phối hợp với TV3 (Vinh) về logic trạng thái đơn khi cháy món và TV6 (Quyên) để nghiệm thu test contract.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu không xét trường hợp người chơi vừa gửi nút `shop_done` vừa có lệnh `buy` trong cùng một tick kết thúc. Tôi đã rà soát lại PRD 4.5 và điều chỉnh logic để ưu tiên xử lý `buy` hoàn tất trước khi kích hoạt `shop_done`.
- **Điều tôi học được:**
  - Thiết kế state machine tách bạch giữa trạng thái hiển thị tức thì (`upgrades`) và trạng thái hiệu lực theo chu kỳ game (`active_upgrades`), cùng cách mở rộng tính năng mô phỏng bằng tham số cấu hình tùy chọn (`burn_s`).

## Phase 3
- **Tôi đã làm:**
  - Cập nhật và kiểm chứng toàn diện logic Bếp và Thanh toán cho kho cá thể (`fresh_stock`): tiêu thụ đúng ID cá thể đang giữ, chốt `base_price = floor(giá * avg_fresh / 100)` với thứ tự thực thi chuẩn (hao tươi xảy ra trước interact trong tick), sắp xếp danh sách `items` trong sự kiện `cook_started` theo `kind` rồi `id`.
  - Kiểm chứng cơ chế tính tiền boa `tip = floor(base_price * 0.2)` dựa trên giá đã chốt theo độ tươi, cộng uy tín khi thu tiền boa dương và thanh toán tức thì khi đóng ca.
  - Tương thích hóa mở rộng Cháy món (`burn`): tự động giải phóng bếp khi tuổi món > 1200 tick và re-reserve cá thể khả dụng tươi nhất (`fresh >= 30`), bỏ qua hàng đã ươn.
  - Cập nhật `ShopSim.snapshot()` để hỗ trợ kho dạng danh sách cá thể (`list[dict]`) phục vụ hiển thị và bàn giao ngày mới.
  - Viết bộ test `tests/test_tv4_phase3.py` bao phủ toàn diện các ca biên: nấu nhiều nguyên liệu, tính giá theo fresh, ngưỡng ươn 30, hòa id khi ươn, cháy món và snapshot Shop.
- **Tôi đã review:**
  - Rà soát chéo mã nguồn Lát 3 (`fresh_stock.py` và quản lý giữ chỗ) với TV3 (Nguyễn Ngọc Vinh), kiểm tra tính tương thích giữa cơ chế giữ chỗ và tương tác lấy đơn của bếp B1/B2.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu tính giá chốt `base_price` của món ăn dựa trên độ tươi lúc bắt đầu tick mà không tính đến việc hao tươi kho xảy ra trước hành động tương tác nấu trong cùng một tick (làm độ tươi giảm đi 1/240 điểm). Khi chạy test kiểm tra món lẩu cá linh bông điên điển, test báo lệch giá 89 != 90. Tôi đã phát hiện ra nguyên nhân từ thứ tự tick chuẩn của PRD và cập nhật test cùng tài liệu giải thích rõ ràng.
- **Điều tôi học được:**
  - Hiểu sâu về tính tất định và thứ tự ưu tiên của các hệ thống con trong cùng một tick mô phỏng game (simulation pipeline order), cùng kỹ thuật dùng phân số (`Fraction`) để tính toán số học chính xác tuyệt đối mà không bị sai số dấu phẩy động.

## Phase 4
- **Tôi đã làm:**
  - Bổ sung cờ cảnh báo khách sắp giận (`is_angry: true` và `warning: "patience_low"`) khi kiên nhẫn của khách dưới 25% (900 tick) trong snapshot của Quán, giúp TV5 dễ dàng render cảnh báo trực quan trên HUD UI.
  - Tự động xóa cảnh báo khi khách được phục vụ chuyển sang trạng thái ăn (`eating`).
  - Kiểm chứng độ bền vững của Quán và Shop qua nhiều ngày liên tiếp (đảm bảo không rò rỉ bộ nhớ, dọn dẹp kết ca đúng luật, bảo toàn `money`, `earned`, `reputation`, và `upgrades`) sẵn sàng cho bài soak test 10 ngày.
  - Viết bộ unit test `tests/test_tv4_phase4.py` kiểm chứng 100% các tính năng trên (3/3 test PASS).
  - Phối hợp với nhóm rà soát hoàn thiện `docs/retro.md` và kiểm thử toàn hệ thống (141/141 test PASS).
- **Tôi đã review:**
  - Đọc chéo mã nguồn tích hợp soak test của TV1 và kiểm tra giao diện kết nối cảnh báo khách sắp giận với HUD của TV5.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu không khai báo `order_status: "assigned"` khi dựng fixture khách đã có món trên tay trong test nhiều ngày, dẫn đến sim cố gắng giữ chỗ nguyên liệu trong kho rỗng và báo lỗi. Tôi đã phát hiện qua test runner và sửa lại fixture test chuẩn xác.
- **Điều tôi học được:**
  - Kỹ năng tổng kết dự án và chuẩn bị bản phát hành phần mềm hoàn chỉnh (v1.0.0): từ quản lý chu kỳ ngày, kiểm tra hiệu năng, bảo đảm chất lượng qua kiểm thử hồi quy (regression testing) đến viết tài liệu phản tư và phối hợp nhóm Agile/AI-SDLC.

