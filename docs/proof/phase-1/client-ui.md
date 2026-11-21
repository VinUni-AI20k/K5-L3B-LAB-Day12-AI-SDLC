# Kiểm chứng UI Phase 1

Bản UI trên nhánh `codex/client-ui-phase-1`, đối chiếu với commit nền `30fb9a2`.

## Kết quả

| Hạng mục | Kết quả |
|---|---|
| Bộ test Python | **34/34 đạt** với Python 3.12.10 trên Windows. Dùng `python3.exe` tạm cho `headless_cmd` và localhost cho test HTTP. Hai ca mới kiểm xung phím đúng một tick, chuẩn hóa hướng chéo và bàn giao kho. |
| So sánh headless với commit nền | JSONL của `gather` và `quan` seed 1, 600 tick giống từng byte. JSONL cập bến và file kho của fixture seed 42 cũng giống từng byte. |
| Chrome với `chonoi.live` | Chọn được ba chế độ. `S` tăng độ sâu ở sông, `W` tăng trục bắc trong quán, `R` bắt đầu lại ca. Fixture giỏ ban đầu chốt bằng `E`, ghi `{"items":{"bong_sung":2,"ca_loc":1}}` và ca tối đọc đúng file đó. Chế độ buổi tối độc lập nạp kho mẫu khi chưa có file kho. |
| Chrome với snapshot mẫu | Kiểm cảnh báo cạn oxy và ngạt, bắt cá bằng Space, giữ E chỉ qua một snapshot, màn ngất hiện kho rỗng, kho khả dụng trừ phần giữ chỗ, mốc kiên nhẫn 50%, nấu → bưng → phục vụ. Phản hồi hiển thị 40k tiền món và 8k boa, tổng kết 48k doanh thu và 348 điểm. |
| Bố cục | Kiểm ảnh chụp menu, hai cảnh, màn chuyển ca và tổng kết trên Chrome ở 1280 px. Kiểm menu và cảnh sông ở 390 px. Các màn được chạy không tràn ngang và không phát sinh lỗi JavaScript. |

## Chạy lại

- Suite trên Bash: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Trên PowerShell, đặt `$env:PYTHONPATH = 'tests;.'` và dùng bản Python 3 có lệnh `python3` trên PATH để chạy smoke hộp đen.
- Live: `python3 -m chonoi.live --mode gather`. Mở địa chỉ in ra và chọn **Chơi trọn ngày**. Nhấn **E** ở bến rồi chọn **Mở quán** để kiểm tra chuyển kho.
- Snapshot mẫu: `python3 -m http.server 8000 --bind 127.0.0.1` ở gốc repo. Mở `http://127.0.0.1:8000/chonoi/web/?preview=1` và dùng **E** hoặc **Space** để duyệt các snapshot.

`chonoi.live` được mở rộng để phục vụ tệp UI, cung cấp tuning từ contract, nhận xung phím ở 60 Hz và chuyển ca qua file kho. Luật thu hoạch, oxy và vòng đời khách còn TODO ở hai sim trong checkout này, nên các trạng thái đó được kiểm bằng snapshot mẫu. Luồng cập bến, bàn giao kho, di chuyển và hết giờ được kiểm bằng mô phỏng thật.
