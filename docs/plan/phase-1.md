# Kế hoạch Phase 1 (0:00 – 1:00)

- **Mục tiêu:** Hoàn thiện lõi luật chơi Phase 1 (`gather` + `quan`), kiểm mâu thuẫn `scenario.py`, HUD cơ bản trên `chonoi.live`, đủ unit/integration test tất định, hoàn thành tài liệu `verification/phase-1.md` & AI Harness, gắn tag `phase-1` trước **1:00**.
- **Việc / người / phụ thuộc:**
  - **Đợt 1 (0:00 – 0:15):**
    - `M6.1` (Nguyễn Như Duy An — M6): Điền `TEAM.md`, sửa `team_size: 6`, chốt `docs/contracts/README.md` *(chặn mọi task `.2`)*.
    - `M6.2` (An — M6): Đọc PRD-0, ghi `docs/clarify.md`, hỏi giảng viên khi mơ hồ.
    - `M1.1` (Vũ Quang Huy), `M2.1` (Nguyễn Minh Quang), `M3.1` (Phùng Văn Thanh Cao), `M4.1` (Nguyễn Nhật Minh): Viết Spec/AC cho từng module.
    - `M5.1` (Vũ Quang Thanh): Cập nhật `AGENTS.md`, viết 2 skill/hook trong `.agents/skills/`, khởi tạo `docs/ai-usage-log.md`.
  - **Đợt 2 (~0:15 – 0:25, sau `M6.1`):**
    - `M1.2`–`M4.2`: Viết test/scenario từ AC cho M1–M4.
    - `M5.2` (Thanh): Chốt danh sách trường UI đọc / lệnh gửi.
    - `M6.3` (An): Code `chonoi/scenario.py` kiểm mâu thuẫn mức luật + unit test *(hỗ trợ test M3, M4)*.
  - **Đợt 3 (~0:25 – 0:45):**
    - `M1.3` (Huy): Code `dive`/`surface` (làm trước), oxy, ngạt, Máu, ngất.
    - `M2.3a` (Quang): Code giỏ LIFO, cập bến, ghi kho (độc lập) → `M2.3b` (sau `M1.3`): hái mặt nước, bắt cá dưới nước.
    - `M3.3` (Cao): Code dựng khách từ scenario, giữ chỗ, kiên nhẫn.
    - `M4.3` (Minh): Code interact bếp/bàn, nấu, bưng, tiền, tip, uy tín (dùng khách giả để song song với M3).
    - `M5.3` (Thanh): HUD `gather` và `quan` trên `chonoi.live`.
  - **Đợt 4 (~0:45 – 1:00, code freeze 0:45, chốt bằng chứng 0:50):**
    - `M1.4`–`M5.4`: Ghép M3 ↔ M4, chạy test, chụp ảnh `chonoi.live`, nộp bằng chứng vào `docs/proof/phase-1/`.
    - `M6.4`–`M6.6` (An): Test tích hợp `gather` → kho → `quan`, kiểm tất định cùng seed, duyệt checklist & điền `docs/verification/phase-1.md`, chạy toàn bộ test & gắn tag `phase-1`.
- **Rủi ro & giảm thiểu:**
  - Xung đột file `gather.py` (M1 & M2) và `quan.py` (M3 & M4) → Tách `M2.3a`/`M2.3b`, `M4.3` dùng khách giả, pull/merge sớm trước 0:45.
  - Trễ gắn tag do dồn việc Đợt 4 cho M6 → Giữ cứng mốc code freeze 0:45 và nộp bằng chứng trước 0:50.
  - Thiếu GitHub handle trong `TEAM.md` → Điền đủ 6 handle thật và chạy `python tools/check_team.py` xanh ngay trong Đợt 1.

## Spec M3 — Quán: Khách (Phùng Văn Thanh Cao)

Code: `chonoi/sim/quan_customers.py` (gắn vào `QuanSim` qua mixin). Test: `tests/test_quan_customers_m3.py`.

| AC | Nội dung (PRD-0 mục D, E, F) |
|---|---|
| AC-P1-C1 | Khách dựng từ scenario có đủ mặc định: `state=waiting`, `order_tick=0`, kiên nhẫn đầy (`patience_s×60`), `order_status=reserved`, `reserved` = công thức món |
| AC-P1-C2 | Kho khả dụng = tồn vật lý − tổng phần giữ chỗ của mọi đơn |
| AC-P1-C3 | Kiên nhẫn khách đang chờ giảm 1 mỗi tick; thời gian ăn khách đang ăn giảm 1 mỗi tick |
| AC-P1-C4 | Hết kiên nhẫn khi còn giờ → `customer_left` reason `patience`, uy tín + `left_reputation_delta` (kẹp tối thiểu), nhả giữ chỗ, bỏ món của đơn đó ở bếp/tay |
| AC-P1-C5 | Khách mới ở `phase_tick = first_customer_tick + k×customer_interval_s×60`; bàn trống id nhỏ nhất; hết bàn thì bỏ lượt |
| AC-P1-C6 | Món chọn đều theo seed trong các món đủ nguyên liệu khả dụng; không có món → `no_dish`, không tạo khách |
| AC-P1-C7 | Hết ca: khách đang ăn trả ngay (reason `closing`), khách đang chờ rời reason `closing`, không trừ uy tín; không xét khách mới ở bước cuối |
| AC-P1-C8 | `random_customers:false` tắt khách tự sinh; cùng seed → output giống từng byte |

Phối hợp M4 (Nguyễn Nhật Minh): M3 gọi `_pay_customer(c, reason, events)` khi khách ăn xong / hết ca và `_release_order(order_id)` khi khách rời. Bản trong `quan_customers.py` là tối thiểu; M4 thay bằng bản đầy đủ cùng chữ ký (tiền, boa, `tip_reputation`) thì M3 không phải sửa. M4 giữ phần `waiting → eating` khi phục vụ (đặt `state`, `order_status=served`, `eat_ticks_left`, `base_price`, `tip`, xóa `reserved`).
