# DEV 5: GAME VISUALS, HIỆU ỨNG SÔNG NƯỚC & ÂM THANH CHỢ NỔI (`client/ui`)

> **File code phụ trách:** `chonoi/web/index.html` (và các tài nguyên web liên quan)  
> **Nhiệm vụ:** Biến giao diện canvas hình khối đơn điệu thành một thế giới game sông nước miền Tây sống động với hiệu ứng hạt, ánh sáng đèn lồng, camera mượt mà và âm thanh.

---

## 1. YÊU CẦU TÍNH NĂNG GAME CẦN CODE
1. **Đồ Họa Chế Độ Lặn Ban Ngày (`mode: gather`):**
   - **Mặt cắt lòng sông:** Hiệu ứng chuyển màu nước từ xanh ngọc mặt sông dần xuống xanh thẫm đáy sông phù sa. Sóng nước gợn lăn tăn cuộn trôi liên tục.
   - **Út Sen:** Vẽ nhân vật mặc áo bà ba, bơi lội nghiêng theo góc hướng di chuyển (`heading_deg`). Khi lặn sâu, tạo hạt bọt khí (air bubbles) li ti nổi dần lên mặt nước.
   - **Đàn cá & Nút hoa:** Cá linh, cá lóc có vây và đuôi quẫy nhịp nhàng. Cụm Bông Điên Điển vàng óng, Bông Súng hồng tím nở bập bềnh theo sóng nước; khi vừa bị hái thì hiển thị mầm hoa chìm dưới nước.
   - **Bến thuyền:** Chiếc ghe tam bản neo đậu mộc mạc bên cọc gỗ tại vị trí dock.
2. **Đồ Họa Chế Độ Quán Nổi Ban Đêm (`mode: quan`):**
   - **Quán sàn gỗ:** Sàn gỗ mộc nổi trên sông đêm, nước sông đen ánh vàng gợn sóng quanh mạn quán.
   - **Ánh sáng Đèn lồng:** Hiệu ứng radial gradient tỏa ánh sáng vàng ấm áp từ lồng đèn bão treo góc quán và bếp than.
   - **Khói bếp:** Bếp than đỏ rực với các hạt khói/tia lửa bay bổng khi đang nấu lẩu hoặc nướng cá.
   - **Order khách:** Bong bóng gọi món (Order Bubble) bay trên đầu khách, kèm thanh đo kiên nhẫn đổi màu Xanh $\rightarrow$ Vàng $\rightarrow$ Đỏ.
3. **Camera LERP & HUD Trực Quan:**
   - Camera mượt mà: `camX += (playerX - camX) * 0.1`, có giới hạn biên bản đồ không bị lộ khoảng đen bên ngoài.
   - HUD: Thanh Oxy phát sáng, các trái tim Máu, túi đồ thu hoạch có icon và số lượng, bảng tiền vàng và sao uy tín lấp lánh.
4. **Âm Thanh Sông Nước (Web Audio API):**
   - Hiệu ứng âm thanh tổng hợp bằng Web Audio API (không cần tải file ngoài): tiếng nước bì bõm, tiếng lặn ngụp, tiếng ting ting khi thu tiền.

---

## 2. LỆNH CHẠY THỬ TRỰC TIẾP TRÊN TRÌNH DUYỆT
```bash
# Thử chế độ Lặn Sông
py -3 -m chonoi.live --mode gather --port 8000

# Thử chế độ Quán Ăn Đêm
py -3 -m chonoi.live --mode quan --port 8000
```
Mở trình duyệt: `http://localhost:8000/`

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên Frontend Game ("mekong-web-artisan") phụ trách nâng cấp giao diện `chonoi/web/index.html` cho game "Quán Ăn Chợ Nổi".

YÊU CẦU:
- Giữ nguyên cơ chế giao tiếp hiện tại: đọc snapshot từ `/state` và gửi phím qua `/input` (WASD, E, Space, R).
- Nâng cấp toàn diện tầng Render Canvas 2D để biến game thành kiệt tác sông nước miền Tây:
1. Chế độ Gather:
   - Vẽ nền sông nhiều lớp (Parallax): gradient nước sâu, dải sóng nước chuyển động theo hàm Sin, tia sáng mặt trời xuyên qua nước (Caustic rays).
   - Thuyền Út Sen ở bến tàu x = 2, d = 0.
   - Vẽ Út Sen: hình dáng người đội nón lá/áo bà ba, xoay theo góc `heading_deg`. Sinh mảng hạt bọt khí (bubbles) mỗi khi bơi dưới nước.
   - Vẽ cá: vẽ hình cá bơi có vây và đuôi quẫy nhẹ.
   - Vẽ bông súng, điên điển: cánh hoa rực rỡ, nhấp nhô theo sóng.
2. Chế độ Quán:
   - Vẽ sàn gỗ quán nổi, mặt nước đêm xung quanh.
   - Hiệu ứng ánh sáng đèn lồng vàng ấm áp (2D soft lighting tỏa từ các nguồn sáng).
   - Hiệu ứng khói bếp than hồng bốc lên khi bếp đang `cooking`.
   - Bàn ăn gỗ, khách ngồi thuyền cập mạn, bong bóng order hiển thị tên món + thanh kiên nhẫn đổi màu.
3. Camera & HUD:
   - Sử dụng LERP Camera làm mượt: `camera.x += (target.x - camera.x) * 0.08`.
   - Thiết kế lại HUD thanh lịch: thanh Oxy hình ống thủy tinh phát sáng, tim máu, icon tiền, sao uy tín vàng óng.
4. Âm thanh Web Audio API nhẹ:
   - Dùng Oscillator tạo tiếng nước róc rách, tiếng bắt cá và tiếng keng khi được boa tiền.
Hãy cập nhật code trực tiếp vào `chonoi/web/index.html`. Đảm bảo hiệu năng ổn định 60 FPS.
```
