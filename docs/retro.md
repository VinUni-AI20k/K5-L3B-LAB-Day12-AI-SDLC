# Retro nhóm

## Phase 2 (nhanh)
Bản nháp của D (Integrator), nhờ A, B, C bổ sung hoặc sửa trong PR này.
- Điều tốt:
  - Khóa contract v1.1 trước (P2-02) nên A, B, C làm song song ở file riêng (`fish.py`, `monsters.py`, `shop.py`, `quan.py`) mà ít đụng nhau; `main` luôn chạy được sau mỗi PR.
  - Phá thử code bằng cách sửa có chủ đích (mutation) bắt được lỗi test bỏ sót: ở `day.py` một cách phá sống sót (không lọc món theo kế hoạch) dẫn tới test mới; ở `monsters.py` kẽ hở "phát hiện khi đang nổi" được C vá sau review.
  - Smoke hộp đen (`smoke_phase2.py`) và `check_determinism.py` gồm `day` cho bằng chứng chạy thật, không chỉ test trong tiến trình.
- Điều tệ:
  - Đề Ticket-02 không đọc được nên nhiều luật là giả định (`clarify` #7 đến #12) vẫn chờ PO; nếu đề khác thì phải sửa `monsters.py`, kế hoạch Ngày và test.
  - P2-08 (menu, pause, HUD) về sau nhất nên `chonoi.live` chưa chơi được chế độ `day`; ghi chép của A và C (nhật ký AI, hồ sơ) vẫn thiếu, B vẫn dùng tài khoản GitHub khác `TEAM.md`.
  - D vẫn nhận phần việc lớn nhất (đa số commit, `day.py`, smoke, ma trận); AI của D tự sai ở chi tiết pause (nhầm số sự kiện) và chỉ lộ khi chạy thật.
- 1 hành động cho Phase 3: Phase 3 đổi schema kho (breaking, contract v1.2), nên trước khi viết code cả nhóm chốt các câu hỏi còn mở ở `docs/clarify.md` với PO và mỗi người ghi nhật ký AI, hồ sơ trong chính PR của task mình (không để dồn cuối phase).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
