# Ma trận truy vết Phase 1

Kiểm trên `main` sau khi gộp Gather, Quán và HUD. Commit mã nguồn `b772097`, Test Contract v1.0, ngày 21/11/2026.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 | Test ramp, chặn biên, xuống/nổi, oxy, Máu, ngạt và giỏ. | [Log test](../proof/phase-1/tests.txt) | Đạt |
| AC-P1-02 | Test mép bán kính, mọc lại, hồi bắt, ưu tiên bến, ngất rơi LIFO, ghi kho khi kết thúc và giữ file đích khi chạm giới hạn tick. | [Log test](../proof/phase-1/tests.txt), [JSONL Gather](../proof/phase-1/gather.jsonl) | Đạt |
| AC-P1-03 | Test lịch khách, chọn món, giữ hàng, không có món, nhả phần giữ và fixture sai trả mã 2. | [Log test](../proof/phase-1/tests.txt) | Đạt |
| AC-P1-04 | Test từ nấu đến thu tiền, giao đúng hạn, boa và uy tín. Chạy phục vụ với kho Gather thật và fixture bàn gần bếp. | [Log test](../proof/phase-1/tests.txt), [JSONL phiên phục vụ](../proof/phase-1/quan-service.jsonl) | Đạt |
| AC-P1-05 | Mở hai ca trên LiveServer bằng Chrome headless, kiểm nhãn Canvas ở 1280×720 và đối chiếu hướng dẫn chạy, điều khiển, điểm và test trong README. | [Log HUD](../proof/phase-1/browser.txt), [README](../../README.md) | Đạt với fixture trình duyệt |
| AC-P1-06 | Chạy hai tiến trình qua file kho với seed 42, so event bàn giao, file và snapshot Quán tick 0. Chạy lại phiên phục vụ để so JSONL từng byte. | [Lệnh và kết quả](../proof/phase-1/smoke.txt), [file kho](../proof/phase-1/inventory.json), [snapshot Quán](../proof/phase-1/quan.jsonl) | Đạt |

## Đánh giá ngắn

- Bộ test trên Windows với Python 3.13.12 từ `.venv` đạt 72/72. Trình chạy kiểm thử dùng Python của `.venv` cho subprocess và `tmp/run/` cho fixture tạm. Phiên phục vụ ghi `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` và `quan_end`. Tổng thu 72 nghìn.
- Chạy lại smoke bằng cách tạo `tmp/phase-1-smoke/`, chép `dock*.json` và `quan-service*.json` từ thư mục bằng chứng vào đó, rồi chạy các lệnh trong [smoke.txt](../proof/phase-1/smoke.txt). Các snapshot trình duyệt được kiểm tự động với fixture. Phần chơi tay một lượt trọn hai ca chưa có bằng chứng riêng.
- Trên bản tích hợp, Diên có 3 commit nội dung, Khôi 2 và Nhân 1.
