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

