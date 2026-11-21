# Ma trận truy vết Phase 2

Bản kiểm là PR cuối từ `phoenix/p2-day` trên nền `b2719e6`, gồm Gather của Diên (`2e43555`, `c72aecf`), Quán của Nhân (`6a5ccab`), vòng ngày của Khôi (`9783faa`) và bản bật Test Contract v1.1. Kiểm trên Windows với Python 3.13.12 trong `.venv`.

| AC | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 | Kiểm 8 đàn lúc đầu, phản xạ và đổi hướng ở bước 120, sinh mỗi 360 tick, giới hạn 12 đàn, lặp lại cùng seed và hái ở N5/N6. | [Log test](../proof/phase-2/tests.txt), [một Ngày mặc định](../proof/phase-2/day.jsonl) | Đạt |
| AC-P2-02 | Kiểm tuần tra, đuổi, hit, bất tử, recoil, rơi LIFO, ngất và M2 từ Ngày 3. CLI từ chối fixture recoil có hướng sai. | [Log test](../proof/phase-2/tests.txt), [fixture D1–D5](../proof/phase-2/day-multi.jsonl) | Đạt |
| AC-P2-03 | So 2 bếp, 4 bàn và kho Quán tick 0. Test các công thức, giữ nguyên liệu, chọn đơn và lọc món theo kế hoạch trong `day`. | [JSONL Quán](../proof/phase-2/integration.quan.jsonl), [log test](../proof/phase-2/tests.txt) | Đạt |
| AC-P2-04 | Chạy CLI thật qua D1–D5. Kiểm pause, mua oxy và Máu, áp dụng từ Ngày kế, giữ tổng thu, đổi pha đúng tick và đếm Ngày khi Shop đóng. | [Fixture và kết quả](../proof/phase-2/day-multi.jsonl), [lệnh](../proof/phase-2/integration.txt), [log test](../proof/phase-2/tests.txt) | Đạt |
| AC-P2-05 | Chrome headless ở 1280×720, dùng dữ liệu mẫu và thao tác qua UI thật. Kiểm cảnh báo Gather, nấu, bưng, giao, thu 72 nghìn, pause Shop, mua bình oxy và xem tổng kết. | [Log trình duyệt](../proof/phase-2/browser.txt), [scenario](../proof/phase-2/browser.scenario.json) | Đạt với lượt chơi tự động |
| AC-P2-06 | Chạy Gather và Quán là hai tiến trình, so event, file kho và snapshot Quán ở tick 0. Chạy một Ngày mặc định đủ 22.200 tick và lặp D1–D5 để so JSONL từng byte. | [Lệnh và kết quả](../proof/phase-2/integration.txt), [file kho](../proof/phase-2/integration.inventory.json), [log test](../proof/phase-2/tests.txt) | Đạt |

## Kết quả và hồi quy

- 110/110 test đạt. Một Ngày mặc định hoàn thành đúng 22.200 tick trong 0,376 giây trên máy kiểm thử. Mẫu một giây vẽ Gather trong Chrome headless đạt 60 FPS ở 1280×720. Đây là số đo cục bộ với fixture trình duyệt.
- Test P1 còn hiệu lực được chạy cùng v1.1. Cập nhật ba kỳ vọng theo Ticket-02: số đàn đầu ca lấy từ tuning, `day` là mode CLI còn `shop` là pha nội bộ, và `attack`/`photo` đúng kiểu bị bỏ qua khi tắt mở rộng. Tag `phase-1` vẫn ở `ad79355`.
- Chạy lại smoke bằng cách tạo `tmp/phase-2-proof/`, chép các fixture `integration.gather.json`, `integration.inputs.json`, `day-multi.scenario.json` và `day-multi.inputs.json` từ thư mục bằng chứng vào đó, rồi dùng [lệnh đã ghi](../proof/phase-2/integration.txt). Khôi xác nhận commit bàn giao trên `main` trước khi gắn tag.
