# Bằng chứng UI TICKET-02

Nhánh `codex/client-ui-phase-2`, nền `e7afc1e`. Contract của checkout là v1.0. Vòng 5 ngày chạy trên `MockSimV11Adapter` và dữ liệu `chonoi/web/phase2.preview.json`.

- **Trình duyệt.** Chạy `python -m chonoi.live --mode gather`, chọn **Chơi**. Chrome headless đi hết Ngày 1–5 ở 1280×720. Giữ E qua DayIntro và kiểm bếp trống khi vào ca tối. Tạm dừng ở sông, quán và cửa hàng. Ảnh trên Canvas và đồng hồ Shop giữ nguyên khi tạm dừng. Bình oxy chuyển từ đã mua cấp 1, đang dùng cấp 0 sang 45 giây ở Ngày 2. Áo phao mua Ngày 4 cho 4 máu ở Ngày 5. Tổng kết mẫu hiện 910k tổng thu, 460k còn lại, 3,8 uy tín, 1210 điểm và lẩu cá linh bán 4 phần.
- **Hiển thị.** Không có lỗi JavaScript hoặc tràn trang trong các trạng thái được đo ở 1280×720. Kiểm tra cỡ chữ từ 18 px và đo số lần vẽ Canvas trong 1,4 giây. Gather 59,9 FPS, Quan 60,2 FPS trên máy kiểm thử. Hai cảnh tiếp tục dùng Canvas và đồ họa vẽ bằng mã.
- **Bản xem độc lập.** Từ gốc repo, chạy `python -m http.server 8000 --bind 127.0.0.1` rồi mở `http://127.0.0.1:8000/chonoi/web/?preview=2`. Chế độ quán độc lập hiện cả 6 món.
- **Input.** Kiểm tra trực tiếp bằng Node thao tác `buy` chỉ có một frame, tiếp theo là frame vắng `buy`. Phím E đang giữ bị chặn qua chuyển pha cho đến khi nhả. Xung ở bến tạo `gather_end` và chuyển sang EveningIntro, với hai bếp vẫn ở trạng thái `idle`.
- **Hồi quy Phase 1.** `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` đạt 45/45. Trên PowerShell dùng `$env:PYTHONPATH = 'tests;.'` và `python3.exe` tạm trỏ tới Python 3.12.10 để các tiến trình smoke chạy đúng lệnh contract. Chrome cũng xác nhận kho `{"items":{"bong_sung":2,"ca_loc":1}}` đi từ cảnh sáng sang cảnh tối trên sim Phase 1 thật.
- **Đối chiếu từng byte.** JSONL của `gather` và `quan` seed 1, 600 tick, cùng JSONL cập bến và file kho seed 42 giống commit nền `e7afc1e`.

## Điểm nối với live adapter v1.1

Bản triển khai dựng sẵn đường nối qua `chonoi/web/adapter.js`. Cần chốt hai điểm với Integrator khi có contract chính thức.

- `GET /config` trả `contract_version`, `tuning` và `capabilities.campaign_v11`. Chỉ dùng live cho chiến dịch khi adapter xác nhận khả năng chạy v1.1.
- `POST /play` nhận `mode: "day"`. `GET /state` trả Snapshot + Events. Đường nối đề xuất dùng `awaiting` để giữ đồng hồ ở DayIntro, EveningIntro và DayResult đến khi `POST /continue` xác nhận `stage`. Đây là giao diện web cần thống nhất với nhóm.
- `POST /input` nhận chuyển động và các xung phím theo chu kỳ 60 Hz. Các cờ nút trở về false ở frame tiếp theo. `buy` chỉ xuất hiện ở frame mua. Live adapter cần bảo toàn thứ tự và chặn lệnh thuộc pha đã đóng. Client lấy ngày, pha, đồng hồ, uy tín và điểm từ snapshot.

Không có cấu hình mở rộng trong checkout này.

## Đối chiếu sau tích hợp

Trên `881c4c4`, manifest đã lên 1.1. Đã chạy lại adapter snapshot mẫu qua đủ năm ngày, pause và oxy ngày kế. `/config` của live chưa công bố capability campaign. [Kết quả trên main](integration.md#ui-và-live-adapter)
