# Research — Phase 3

| # | Quyết định | Lý do | Loại bỏ |
|---|---|---|---|
| R1 | Fresh nội bộ là số nguyên đơn vị = fresh × 240; gather −2/tick, quán −1/tick; ngưỡng 30 → 7200 | Đề gợi ý; tránh sai số float ở ngưỡng và `floor` | float trực tiếp |
| R2 | Hằng tính từ contract: `units_per_tick = decay_per_s × 240 / tick_hz` (phải ra số nguyên, kiểm khi nạp) | Không hard-code số | — |
| R3 | `inventory.py` có `read_items_v12` / `write_items_v12`; chọn theo `contract_version` | Đề: bên đọc chọn schema theo version; cho phép chuyển dần | Đổi thẳng (vỡ main giữa chừng) |
| R4 | Ghi file: `json.dump` fresh dạng float đầy đủ (`units/240`), tệp tạm cùng thư mục + `os.replace` (đã có trong khung) | Giữ chính xác khi đọc lại | round 3 |
| R5 | Bộ cấp id cá thể `ItemIds` sống ở tầng runner/day, truyền cho `GatherSim` | Id tăng xuyên pha/Ngày | Mỗi sim tự đếm |
| R6 | `spoiled` phát tại bước hao (đầu bước), theo id; giữ chỗ ươn xử lý ngay sau trong quán | Thứ tự tick của đề | — |
| R7 | Thử giữ lại: hàm `_reserve(order)` dùng chung cho đặt món mới và giữ lại | Một luật chọn "tươi nhất, hòa id" | — |
| R8 | Mở rộng `current`, `reservations`: không làm trong lõi P3 | Đề: chọn sau khi độ tươi ổn | — |
