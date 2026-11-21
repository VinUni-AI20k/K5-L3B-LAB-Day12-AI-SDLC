# 05: HUD độ tươi / hàng ươn (Phase 3)

**What to build:** Người chơi nhìn là biết con nào sắp bỏ: số độ tươi hoặc thanh, và dấu hiệu rõ cho hàng đã ươn — trong giỏ lẫn trong kho quán.

**Blocked by:** 01 (mềm: 02, 03 — thiếu trường thì fallback)

**Status:** done (ready-for-review)

- [x] Giỏ buổi sáng: mỗi ô hiện độ tươi (thanh mini trực quan), đổi màu theo ngưỡng 30 (xanh $\ge 70$, vàng $30-70$, đỏ $< 30$); cá thể ươn có nhãn gạch chéo đỏ và chữ `ƯƠN`.
- [x] Kho quán + Shop: hiện độ tươi từng cá thể, hàng ươn bị làm mờ/gạch và có cảnh báo riêng không gợi ý nấu.
- [x] `spoiled` hiện thông báo toast ngắn đúng một lần cho mỗi cá thể (không spam khi đang hao liên tục) kèm âm thanh cảnh báo.
- [x] Có `?fx=0` tắt hiệu ứng nặng (tắt particles và wave deformation); không che vùng chơi.
- [x] Thiếu trường `fresh` (chạy v1.0/1.1) thì HUD ẩn phần độ tươi, hoàn toàn `null-safe`, không văng lỗi.
- [x] Không thêm mã vào `chonoi/`; headless không đổi một byte.
