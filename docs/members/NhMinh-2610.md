# NhMinh-2610 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - **Phase 1** (`7a57f3b`, `7f31375`, `06d8ef5`, `b42538f`): Chốt AC, viết 12 test `tests/test_quan_m4.py`, cài luật bếp/bàn/bưng/tiền/tip/uy tín/hết ca trong `chonoi/sim/quan.py` và ghép `CustomerMixin` của M3 (68/68 test xanh).
  - **Phase 2** (`0f46a50`, `9a1f5e9`, `55a66fb`, `12c98f5`, `d29de32`, `41d199a`): Viết `spec-p2-m4.md`, cài `chonoi/sim/shop.py`, `chonoi/sim/day.py`, Pause 3 mode trong `chonoi/runner.py`, bổ sung test CLI hộp đen `tests/test_day_shop_pause_m4.py` (gồm Ngày 3 sinh `M2`, ngất mở quán kho rỗng), ghép M1+M3 đạt 110/110 test xanh.
  - **Phase 3–4 chuẩn bị sớm** (`b194801`): Chốt `spec-p3-m4.md` (giá theo độ tươi `fresh_units`) và dựng trước `chonoi/soak.py` (bot tất định 10 Ngày).
- **Tôi đã review:** Kiểm tra chéo `quan_customers.py`, `test_quan_customers_m3.py`, `test_day_m3_integration.py` với Cao (`ththanh8888`) và điểm nối `day` với Huy (`huyvu-03`).
- **AI sai ở đâu & phát hiện thế nào:** Khi nâng v1.1 thêm bếp `B2 [5, 8]`, test P1 cũ dùng `[3.51, 8]` vô tình lọt tầm `B2`; chạy regression phát hiện ngay và dời sang phía tây `B1` (`[0.5, 8]`/`[0.49, 8]`).
- **Bài học:** Tách sạch module (`shop.py`, `day.py`, `quan_customers.py`) và chạy regression sau mỗi lần pull giúp ghép 6 người gần như không conflict.
