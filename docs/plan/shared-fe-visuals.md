# PHẦN VIỆC CHUNG CỦA NHÓM: GIAO DIỆN WEB & ĐỒ HỌA CHỢ NỔI (`client/ui`)

> **File phụ trách:** `chonoi/web/index.html`  
> **Quy ước:** Đây là **CÔNG VIỆC CHUNG** của cả nhóm. Bất kỳ ai rảnh tay hoặc sau khi code xong phần gameplay của mình đều có thể đóng góp làm đẹp giao diện, gắn sprite, hiệu ứng nước, khói bếp và âm thanh.

---

## 1. MỤC TIÊU HIỂN THỊ
Biến giao diện web chơi thử từ hình khối tạm thời (khối vuông/tròn thô sơ) thành một **trải nghiệm game sống động mang đậm phong cách Dave the Diver miền Tây sông nước**.

### Các lát hiển thị có thể cùng nhau đóng góp:
1. **Đồ Họa Lặn Sông Ban Ngày (`mode: gather`):**
   - Nền lòng sông Parallax: mặt nước phản chiếu nắng vàng, lặn sâu chuyển dần sang xanh thẫm phù sa.
   - Nhân vật Út Sen bơi lội nghiêng theo góc `heading_deg`, sủi bọt khí (bubbles) khi lặn dưới nước.
   - Bè Bông Điên Điển vàng ươm, Bông Súng nở hồng nhấp nhô theo sóng nước; đàn cá linh, cá lóc quẫy vây mềm mại.
   - Ghe tam bản neo đậu mộc mạc ở bến tàu (`dock_pos`).
2. **Đồ Họa Quán Ăn Nổi Ban Đêm (`mode: quan`):**
   - Quán sàn gỗ nổi lập lờ trên sông đêm, nước sông đen ánh vàng gợn sóng quanh mạn quán.
   - Ánh đèn lồng/đèn bão tỏa sáng vàng ấm cúng, hạt khói bếp than hồng bay bổng khi nấu lẩu hoặc nướng cá.
   - Khách ngồi bàn ăn, order bubble hiện icon món rõ ràng kèm thanh đo kiên nhẫn đổi màu Xanh $\rightarrow$ Vàng $\rightarrow$ Đỏ.
3. **Camera LERP & HUD Trực Quan:**
   - Camera mượt mà: `camX += (playerX - camX) * 0.1` bám theo Út Sen.
   - HUD: Thanh Oxy phát sáng, các trái tim Máu, túi đồ thu hoạch, bảng tiền vàng và sao uy tín lấp lánh.
4. **Âm Thanh Sông Nước (Web Audio API):**
   - Tiếng nước róc rách, tiếng thở bình dưỡng khí, tiếng xèo xèo bếp than và tiếng leng keng khi nhận tiền boa.

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

## 3. PROMPT COPY-PASTE CHO AI AGENT KHI NÂNG CẤP GIAO DIỆN
```text
Bạn là lập trình viên Frontend Game ("mekong-web-artisan") phụ trách nâng cấp giao diện `chonoi/web/index.html` cho game "Quán Ăn Chợ Nổi".

YÊU CẦU KIẾN TRÚC:
- Client là View thụ động: CHỈ ĐỌC snapshot từ `GET /state` và gửi phím qua `POST /input` (WASD, E, Space, R).
- Không can thiệp vào logic tính toán va chạm hay quy tắc sim của backend.

NHIỆM VỤ NÂNG CẤP ĐỒ HỌA:
1. Chế độ Gather:
   - Vẽ nền sông Parallax: dải sóng nước chuyển động theo hàm Sin, tia sáng mặt trời xuyên qua nước.
   - Vẽ Út Sen mặc áo bà ba, nón lá, bơi uyển chuyển theo góc `heading_deg`. Sinh hạt bọt khí nổi lên mặt nước khi lặn.
   - Vẽ cá linh/cá lóc có vây và đuôi quẫy nhẹ; vẽ cụm bông súng, điên điển rực rỡ dập dềnh theo sóng.
2. Chế độ Quán:
   - Vẽ sàn gỗ nổi, mặt nước đêm xung quanh.
   - Hiệu ứng ánh sáng đèn lồng tỏa quầng sáng vàng ấm áp.
   - Hạt khói bốc lên từ bếp than hồng khi bếp `cooking`.
   - Bong bóng order món ăn trên đầu khách kèm thanh kiên nhẫn đổi màu.
3. Camera & HUD:
   - Camera LERP làm mượt: `camera.x += (target.x - camera.x) * 0.08`.
   - HUD thanh lịch: thanh Oxy hình ống thủy tinh phát sáng, tim máu, icon tiền, sao uy tín vàng óng.
Hãy cập nhật code trực tiếp vào `chonoi/web/index.html`. Đảm bảo hiệu năng ổn định 60 FPS.
```
