# LETHESHIYING — phản tư cá nhân (≤ 200 từ)

> Bản nháp sau Phase 1; cập nhật cuối buổi.

- Tôi đã làm (kèm link commit):
  - Gather lát 2: hái nút và bắt cá trong `chonoi/sim/gather_harvest.py` ([e04b3fa](../../../../commit/e04b3fa)).
  - 16 test hộp đen cho lát 2 ([529642d](../../../../commit/529642d)). Toàn bộ test: 57 OK.
- Tôi đã review (kèm link): (bổ sung khi review PR của các lát khác)
- AI sai ở đâu và tôi phát hiện thế nào: AI viết hai test sai (đặt cá ở mặt nước nên headless từ chối; bấm `catch` hai lần liền không có frame thả nên không có cạnh lên). Tôi chạy test, thấy đỏ, đọc lỗi rồi sửa test; luật không phải sửa.
- Điều tôi học được: input `interact`/`catch` tính theo cạnh lên, và phần giả định chưa rõ (giỏ không đủ chỗ thì cá ở lại, không hồi chiêu) phải ghi cho PO xác nhận thay vì tự quyết.
