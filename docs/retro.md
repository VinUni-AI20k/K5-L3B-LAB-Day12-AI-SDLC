# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt:
  - Tất cả 5 thành viên chia việc rõ ràng theo PRD v1.1 và hoàn thành đúng hạn (TV1: quái vật Cá Sấu; TV2: đàn cá bơi & sinh; TV3: quán mở rộng & lọc thực đơn; TV4: vòng lặp ngày & shop & pause; TV5: QA Lead & HUD cá sấu).
  - Tích hợp không bị xung đột logic lõi; toàn bộ 78/78 tests đều PASS ngay lần đầu chạy tích hợp đầy đủ.
  - Chế độ headless duy trì tính tất định 100% byte-identical across runs.
- Điều tệ:
  - Nhánh `feat/p2-day` tích hợp song song cả TV3 và TV4 nên cần cẩn trọng khi merge kiểm chứng.
  - Trình duyệt web có lúc bị đen màn hình do lỗi cú pháp JS khi sửa code canvas nếu không kiểm tra kỹ biến trùng.
- 1 hành động cho Phase 3:
  - Viết script tự động chạy cú pháp JS (`node -c`) và kiểm tra test tổng hợp trước mỗi lần commit giao diện và tính năng.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
