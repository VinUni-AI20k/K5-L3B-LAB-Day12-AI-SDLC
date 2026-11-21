# Ma trận kiểm chứng Phase 2

Các mã dưới đây là mã theo dõi của nhóm. Khi bàn giao, ghi commit `main` gắn tag, lệnh hoặc cách kiểm, đường dẫn bằng chứng thực tế và kết quả đạt/chưa đạt.

| AC | Tiêu chí | Cách kiểm / bằng chứng cần lưu | Kết quả |
|---|---|---|---|
| AC-P2-01 | Manifest v1.1 dùng đúng số chuẩn, 6 nguyên liệu, 6 món và kế hoạch D1–D5. | Đối chiếu manifest với Ticket 02, tính lại tổng nguyên liệu từ công thức. | Chưa kiểm v1.1 |
| AC-P2-02 | Khởi tạo 8 đàn tại 8 tọa độ khác nhau, bơi/đổi hướng/phản xạ và sinh đúng lịch. | Fixture mép/góc, bước bơi thứ 120, tick sinh 360, trần 12, khoảng cách bằng 1 m và cờ tắt. So byte hai lượt cùng đầu vào. | Chưa kiểm v1.1 |
| AC-P2-03 | Cá Sấu, LIFO, bất tử, ngạt và chuyển Quán khi ngất. | Kiểm M1/M2 theo Ngày, ngưỡng phát hiện/rời chase, một hit mỗi bước, recoil, hit cùng tick với ngạt và kho rỗng khi chết. | Chưa kiểm v1.1 |
| AC-P2-04 | Quán chạy riêng có 2 bếp, 4 bàn, đủ 6 món. | Fixture nhiều bàn/bếp, giữ chỗ, chọn mục tiêu, nấu, giao, thu tiền và khách rời lúc đóng ca. | Chưa kiểm v1.1 |
| AC-P2-05 | Ngày công bố kế hoạch và Quán lọc món theo kế hoạch. | So `day_plan` D1–D5 và override; thử có nguyên liệu cho món ngoài kế hoạch, gọi vượt số suất dự kiến và fixture Quán mâu thuẫn sau bàn giao. | Chưa kiểm v1.1 |
| AC-P2-06 | Đủ vòng Ngày và Shop, giữ tiền/`earned`/uy tín, cấp có hiệu lực đúng Ngày. | Smoke 1 và 5 Ngày, mua đủ giá/thiếu tiền/tối đa, mua rồi đóng cùng bước cuối, snapshot đổi pha và thứ tự event. Kiểm chỉ tăng `days_completed` khi Shop đóng. | Chưa kiểm v1.1 |
| AC-P2-07 | Chạy hai tiến trình với kho cũ và kho có nguyên liệu mới; các luật P1 còn hiệu lực vẫn đạt. | Lưu `integration.*` và log hồi quy. Ghi lý do sửa test do luật mới hoặc sửa fixture sai hợp đồng. | Chưa kiểm v1.1 |
| AC-P2-08 | Pause và input giữ đúng cạnh/tick qua pha. | Thử cả ba mode, pause trong Shop, buy trong pause, giữ nút qua pha và resume kèm hành động. | Chưa kiểm v1.1 |
| AC-P2-09 | Menu, intro, DayResult, Shop, Summary và HUD chơi được, đạt mốc hiệu năng. | Chơi thử tại 1280×720, lưu ảnh hai HUD và màn Shop/pause, số đo FPS trung bình và thời gian headless một Ngày. | Chưa kiểm v1.1 |

## Baseline trước triển khai

- Commit khảo sát `41f10eb`, manifest v1.0. Lệnh test chung chạy 55 test, 50 qua, 4 fail vì fixture Quán, 1 lỗi do môi trường chặn mở socket Live Server.
- Fixture đang lỗi gồm 3 ca khai timer ăn dương khi khách còn `waiting` và 1 ca món chín tham chiếu khách `C1` chưa được dựng. Người 3 sửa trạng thái fixture theo hợp đồng và giữ các assert hành vi. Người 2 nối module tài nguyên vào Gather rồi thêm ca end-to-end hái và bắt; test module riêng đã qua ở baseline.
- Chưa thấy tag `phase-1` ở checkout hiện tại. Chưa xác minh được tag trên fork vì môi trường không phân giải được GitHub.
