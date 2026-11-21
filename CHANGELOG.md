# Changelog

## Unreleased

### Phase 4
- Khai `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`) ở gốc `game.contract.json`.
- `contract_version` giữ `"1.1"`. Bản `"1.3"` chỉ bật khi kho cá thể đã là schema đang chạy (gameplay vẫn theo v1.2). Gắn tag và Release chờ TV5 báo regression xanh.

### Phase 3
- **Breaking change (chưa bật):** từ `contract_version` `"1.2"`, file kho đếm `{"items":{kind:n}}` trả mã 2. Schema mới là `{"items":[{"id","kind","fresh"}]}`.
- `chonoi/inventory.py` đọc/ghi cả hai schema theo version. Fixture cũ cập nhật bằng cách đổi mỗi món đếm thành một cá thể `fresh: 100` (hoặc giá trị scenario), id `I1`, `I2`, … không trùng.
- `tuning.freshness`: initial 100, giỏ −0.5/s, quán −0.25/s, ươn khi fresh < 30. Nội bộ 240 đơn vị/điểm.

### Phase 2
- Contract `"1.1"`: số chuẩn, 6 món, cá bơi/sinh, kế hoạch D1–D5, shop, Cá Sấu trong tuning.

### Phase 1
- Khung headless gather/quan, kho đếm, smoke Test Contract.
