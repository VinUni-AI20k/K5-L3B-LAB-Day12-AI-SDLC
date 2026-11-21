# 06: Menu / intro / result / HUD / pause UI

**What to build:** Người chơi nhìn là hiểu mình đang ở đâu: menu chính, intro kế hoạch của Má Tư, HUD hai buổi có "đã lấy/cần", cảnh báo Cá Sấu, màn kết quả ngày, tổng kết sau Ngày 5, và pause làm mờ nền.

**Blocked by:** 01 (đọc snapshot có `day`; thiếu trường thì fallback)

**Status:** ready-for-agent

- [ ] Menu chính có **Chơi** và **Thoát**; DayIntro hiện Ngày + danh sách món/số suất, tự chuyển sau 4 s hoặc khi nhấn phím; EveningIntro hiện số lượng nhập kho và món nấu được.
- [ ] DayResult hiện khách đã phục vụ / bỏ đi, tiền, boa, thay đổi uy tín; Summary sau Ngày 5 hiện tổng tiền, tổng điểm, uy tín, món bán chạy.
- [ ] Pause bằng Esc/P: làm mờ nền, có **Tiếp tục** và **Về menu**; khi pause đồng hồ và mọi timer gameplay đứng yên (kể cả trong Shop).
- [ ] HUD sáng: Máu, oxy (dưới 25% đổi màu/nhấp nháy), thời gian (≤ 30 s đổi màu), độ sâu, giỏ theo loại, **danh sách cần lấy (đã lấy/cần)**, hồi bắt; gợi ý hái/cập bến khi tới gần; "Thủy quái!" + viền tím khi quái gần; "Hết hơi!" khi oxy cạn.
- [ ] HUD tối: đồng hồ ca, tiền ca, uy tín, món + kiên nhẫn từng bàn (đổi màu khi < 25%), tiến độ bếp/trạng thái món chín, món đang cầm, kho khả dụng.
- [ ] HUD Shop: tiền, danh sách nâng cấp kèm giá và cấp hiện tại, phím mua, đồng hồ tự đóng.
- [ ] Chữ không chân ≥ 18 px ở 1280×720; trung bình ≥ 30 FPS; có `?fx=0` tắt hiệu ứng nặng.
- [ ] Không thêm mã nào vào `chonoi/`; headless vẫn cho JSONL giống từng byte.
