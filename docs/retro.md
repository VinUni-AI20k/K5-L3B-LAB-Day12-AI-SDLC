# Retro nhóm

## Phase 2 (nhanh)
Bản nháp của D (Integrator); TuHoAnh và Cuongngucuteee đã thêm phần của mình, A bổ sung hoặc sửa.
- Điều tốt:
  - Khóa contract v1.1 trước (P2-02) nên A, B, C làm song song ở file riêng (`fish.py`, `monsters.py`, `shop.py`, `quan.py`) mà ít đụng nhau; `main` luôn chạy được sau mỗi PR.
  - Phá thử code bằng cách sửa có chủ đích (mutation) bắt được lỗi test bỏ sót: ở `day.py` một cách phá sống sót (không lọc món theo kế hoạch) dẫn tới test mới; ở `monsters.py` kẽ hở "phát hiện khi đang nổi" được C vá sau review.
  - Smoke hộp đen (`smoke_phase2.py`) và `check_determinism.py` gồm `day` cho bằng chứng chạy thật, không chỉ test trong tiến trình.
  - **Cuongngucuteee:** P2-04 qua review của D chỉ sau một vòng (thêm test mặt nước); P2-08 có ảnh chụp trình duyệt thật làm bằng chứng và nhờ đó tìm ra lỗi ghi đè lệnh mua.
  - **TuHoAnh:** Hoàn thành `P2-05` đúng Test Contract v1.1 (2 bếp, 4 bàn, 6 món, lọc `allowed_dishes`), pass 193/193 test và `check_no_hardcode.py` sạch.
- Điều tệ:
  - Đề Ticket-02 không đọc được nên nhiều luật là giả định (`clarify` #7 đến #12) vẫn chờ PO; nếu đề khác thì phải sửa `monsters.py`, kế hoạch Ngày và test.
  - P2-08 (menu, pause, HUD) về sau nhất nên `chonoi.live` chơi được chế độ `day` rất muộn; ghi chép của A và C (nhật ký AI, hồ sơ) vẫn thiếu, B vẫn dùng tài khoản GitHub khác `TEAM.md`.
  - **TuHoAnh:** Ở Phase 1 bị conflict khi merge `origin/main` do chưa kéo `main` trước lúc làm nhánh nối; đầu Phase 2 hơi chậm nhịp khi chờ `game.contract.json` v1.1.
  - **Cuongngucuteee:** P2-04 và P2-08 vào `main` muộn (sau smoke phút 20); test ban đầu của tôi có kẽ hở (chỉ kiểm tick cuối) nên phải sửa sau review; chưa chơi tay trọn một Ngày bằng bàn phím; hồ sơ và nhật ký AI để tới cuối phase mới ghi.
  - D vẫn nhận phần việc lớn nhất (đa số commit, `day.py`, smoke, ma trận); AI của D tự sai ở chi tiết pause (nhầm số sự kiện) và chỉ lộ khi chạy thật.
- 1 hành động cho Phase 3: Phase 3 đổi schema kho (breaking, contract v1.2), nên trước khi viết code cả nhóm chốt các câu hỏi còn mở ở `docs/clarify.md` với PO và mỗi người ghi nhật ký AI, hồ sơ trong chính PR của task mình (không để dồn cuối phase).
  - **Cuongngucuteee:** Mỗi test luật mới phải phá thử ít nhất một lần trước khi mở PR; HUD độ tươi (AC-P3-05) đẩy sớm, trước smoke phút 20.
  - **TuHoAnh:** Luôn `git fetch` + `merge origin/main` và chạy đủ `unittest` + `check_no_hardcode.py` trước mọi lần mở PR.

## Phase 3 (nhanh)
A gom và nộp (P3-10); mỗi người tự thêm dòng của mình.
- Điều tốt:
  - **Cuongngucuteee:** HUD độ tươi (P3-06) làm song song với gather và quán nhờ D gộp schema kho cá thể (P3-02) trước và ghi dạng snapshot trong hợp đồng; test dùng thẳng adapter của P3-02 nên không tự bịa dữ liệu.
- Điều tệ:
  - **Cuongngucuteee:** Mã việc trên Sheet lệch 1 so với kế hoạch nên tôi đặt nhầm tên hai PR (#39, #42); chưa thử HUD với sim v1.2 thật vì quán chưa xong.
- 1 hành động cho Phase 4:
  - **Cuongngucuteee:** Trước khi làm, đối chiếu mã việc trên Sheet với commit đã gộp; khi A, B gộp v1.2 thì mở cửa sổ chơi chụp lại HUD độ tươi.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
