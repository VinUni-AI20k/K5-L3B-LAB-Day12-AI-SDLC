# BẢNG TỔNG HỢP PHÂN CÔNG 5 ĐẦU VIỆC LÀM GAME (DEV 1 -> DEV 5)

> **Cảm hứng thiết kế:** Game lấy cảm hứng từ **Dave the Diver** phiên bản Miền Tây Sông Nước:
> - **Sáng:** Lặn sông Mekong (Blue Hole) bắt Cá Linh, Cá Lóc, hái Bông Súng, Bông Điên Điển, quản lý bình Oxy & Giỏ đồ, cập bến an toàn.
> - **Tối:** Mở Quán Ăn Chợ Nổi (Bancho Sushi), đón khách ghe, nổi lửa nấu lẩu/cá nướng, bưng bê phục vụ trước khi khách hết kiên nhẫn, thu tiền & điểm uy tín.
>
> **Quy tắc làm việc:** Cả 5 người trong team tự do chọn 1 trong 5 đầu việc bên dưới. Ai nhận việc nào thì điền Tên và GitHub Handle của mình vào bảng.

---

## BẢNG CHỌN TÍNH NĂNG GAME (MỞ CHO CẢ 5 THÀNH VIÊN)

| STT | Tên Tính Năng Game | Module File | Thành viên nhận việc | GitHub Handle | Trạng thái | File hướng dẫn & Prompt AI |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **DEV 1** | **Gameplay Lặn & Sinh Tồn** (Bơi, Oxy, Ngạt nước, Máu, Ngất xỉu, Cập bến ghe) | `chonoi/sim/gather.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-1-gather-survival.md`](./task-1-gather-survival.md) |
| **DEV 2** | **Gameplay Săn Bắt & Sinh Thái Sông** (Hái Bông Súng/Điên Điển mọc lại, Săn Cá Linh/Cá Lóc, Giỏ LIFO) | `chonoi/sim/gather.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-2-gather-harvest.md`](./task-2-gather-harvest.md) |
| **DEV 3** | **Gameplay Quán Ăn: Thực Khách & Menu** (Khách ghé ghe, Xếp bàn, Check món theo kho, Giữ chỗ, Kiên nhẫn) | `chonoi/sim/quan.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-3-quan-customers.md`](./task-3-quan-customers.md) |
| **DEV 4** | **Gameplay Quán Ăn: Nấu Bếp & Kinh Tế** (Bếp nổi lửa, Bưng bê món, Phục vụ khách ăn, Tiền, Tip, Uy tín) | `chonoi/sim/quan.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-4-quan-kitchen.md`](./task-4-quan-kitchen.md) |
| **DEV 5** | **Game Visuals & Âm Thanh Chợ Nổi** (Vẽ Út Sen, Sóng nước sông Tiền, Quán nổi đèn lồng đêm, Khói bếp, Camera LERP) | `chonoi/web/index.html` | *(Chưa nhận)* | `@...` | `Trống` | [`task-5-game-visuals.md`](./task-5-game-visuals.md) |

---

## HƯỚNG DẪN DÀNH CHO AI AGENT KHI ĐỌC REPO NÀY
1. **Xác định vai trò của bạn:** Đọc bảng trên để biết người dùng của bạn đang phụ trách vị trí DEV nào (DEV 1 $\rightarrow$ DEV 5).
2. **Đọc tài liệu nhiệm vụ:** Mở ngay file hướng dẫn tương ứng (`task-1-*.md` đến `task-5-*.md`) để nắm rõ các hàm, biến và sự kiện cần code.
3. **Quy tắc kiểm thử:** Trước khi báo hoàn thành, luôn chạy lệnh test:
   - Windows: `py -3 -m unittest discover -s tests -v`
   - Linux / Mac: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   Đảm bảo 100% test cases đều pass (xanh), không làm vỡ các trường dữ liệu trong snapshot.

---

## NGUYÊN TẮC LÀM GAME SONG SONG (KHÔNG XUNG ĐỘT)
1. **Tạo nhánh riêng theo việc:**
   - Dev 1: `git checkout -b feat/gather-survival`
   - Dev 2: `git checkout -b feat/gather-harvest`
   - Dev 3: `git checkout -b feat/quan-customers`
   - Dev 4: `git checkout -b feat/quan-kitchen`
   - Dev 5: `git checkout -b feat/game-visuals`
2. **Quy định commit:** Mỗi thành viên commit tối thiểu 3 lần từ tài khoản GitHub của mình.
3. **Chạy test kiểm tra trước khi push:**
   - Windows: `py -3 -m unittest discover -s tests -v`
   - Linux / Mac: `python3 -m unittest discover -s tests -v`
