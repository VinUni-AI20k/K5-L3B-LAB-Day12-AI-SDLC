# justapea25 — phản tư cá nhân (≤ 200 từ)

> Bản nháp sau Phase 1; cập nhật cuối buổi.

- Tôi đã làm (kèm link commit):
  - Gather lát 1: oxy, ngạt, Máu, ngất, giỏ LIFO ([c90067c](../../../../commit/c90067c), test [e7e16b0](../../../../commit/e7e16b0), PR [#1](../../../../pull/1)).
  - Dựng khung chung để cả nhóm làm song song không conflict: tách file lát 2–4, hợp đồng khách và sự kiện, TEAM/nhật ký AI/clarify ([998cfd5](../../../../commit/998cfd5), [9e34f4e](../../../../commit/9e34f4e), [30d0b2d](../../../../commit/30d0b2d), PR [#2](../../../../pull/2)).
- Tôi đã review (kèm link): (bổ sung khi review PR của các lát khác)
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test dựng scenario ở mặt nước với bộ đếm ngạt > 0, bị headless từ chối (mã 2). Tôi chạy toàn bộ test, thấy đỏ, đọc lỗi và đổi scenario thành bắt đầu dưới mặt nước rồi bơi lên.
- Điều tôi học được: chốt hợp đồng (tên hàm, schema, sự kiện) và chia file theo người ngay từ đầu giúp nhóm đông làm song song mà gần như không conflict.
