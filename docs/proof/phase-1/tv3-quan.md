# Kiểm thử Lát 3 Quán

PowerShell, từ thư mục gốc của repo:

```powershell
$env:PYTHONPATH='tests;.'
python -m unittest discover -s tests -v
$tv3Out = Join-Path ([System.IO.Path]::GetTempPath()) ('quan-tv3-' + [guid]::NewGuid() + '.jsonl')
python -m chonoi.headless --mode quan --seed 42 --inventory docs/contracts/inventory.sample.json --ticks 3720 --snapshot-every 120 --out $tv3Out
```

- **Unittest** — 36 test qua, gồm 4 test mới về giữ kho, thiếu nguyên liệu, khách rời đúng hạn và fixture giữ quá kho. Workspace khi chạy có thay đổi sẵn trong `tests/helpers.py`.
- **Headless** — mã thoát 0. Tick 120 phát `customer_arrived` cho C1 gọi `ca_loc_nuong_trui`. Tick 3720 phát `customer_left` cho C1 rồi `customer_arrived` cho C2 gọi `goi_bong_sung`.
- **Tính tất định** — chạy lệnh headless trên hai lần với hai đường dẫn đầu ra. Cả hai JSONL có SHA-256 `143ad5f06d8ddfcdbbd6b60c32402c10451ff315693efb6bc41ee856f9b50e87`.
- **Fixture sai** — chạy Quán với `--ticks 0 --scenario` chứa `{"quan":{"customers":[{"id":"C1","table_id":"T1","dish_id":"goi_bong_sung"}]}}`. Tiến trình trả mã 2 vì lượng giữ vượt kho và không tạo JSONL đầu ra.

TV4 có thể dùng `available_stock()` để đọc kho khả dụng. Hai lời gọi `_update_customer_patience(events)` và `_spawn_customer(events)` hiện được nối vào `step()` để chạy Lát 3 qua headless. TV4 sẽ dùng các điểm nối này khi ghép bếp và tương tác.

Bản triển khai dùng `waiting` cho đơn mới, giảm kiên nhẫn ở `waiting` và `assigned`, và xử lý khách rời trước khi sinh khách mới. Cần đối chiếu tên trạng thái, payload sự kiện và thứ tự xử lý với bản đầy đủ mục F trước khi nghiệm thu.

## Bảo quản món khi chơi trực tiếp

Đã chạy lại lệnh unittest ở trên sau khi ghép bản TV4. **39 test qua**, gồm ba test mới kiểm tra thời hạn trong cấu hình live, trả và dùng lại món với kho rỗng, và tự hủy đúng tick hết hạn. Ca hết hạn đặt đồng hồ mô phỏng ngay trước mốc để kiểm tra chính xác hai tick liền kề. Một ca thường dài 180 giây game, nên ca mới qua lệnh chơi lại khởi tạo kho bảo quản mới. Chưa có cơ chế lưu món qua nhiều ca.
