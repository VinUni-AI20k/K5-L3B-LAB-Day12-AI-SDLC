# Ma trận truy vết Phase 3

Kiểm bản `phoenix/p3-integration` trên nền `d720282`, dùng adapter từ `6e12f33` và Quán từ `e58cd7a`. Kết quả chạy cục bộ trên Windows bằng Python trong `.venv`.

| AC | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 | Mẫu kho v1.1/v1.2, đọc thập phân chính xác, ID trùng, loại lạ, giá trị ngoài miền và xuất file nguyên tử. | [Log test](../proof/phase-3/tests.txt), [file kho](../proof/phase-3/inventory.json) | Đạt |
| AC-P3-02 | Gather hao đầu tick, qua ngưỡng 30 ở tick 1, giỏ giữ thứ tự nhặt và rơi LIFO. File khớp event kết thúc ca. | [JSONL Gather](../proof/phase-3/gather.jsonl), [log test](../proof/phase-3/tests.txt) | Đạt |
| AC-P3-03 | Giữ ID riêng theo đơn, hao khi đang giữ, cấp lại sau `spoiled`, xử lý thiếu hàng và thứ tự đơn. | [JSONL Quán](../proof/phase-3/price.jsonl), [log test](../proof/phase-3/tests.txt) | Đạt |
| AC-P3-04 | Cá thể I1 ươn, cấp lại I2 và nấu cùng tick. Giá chốt 29 nghìn. Hồi quy boa, giao sát hạn, thanh toán và đóng ca. | [JSONL chốt giá](../proof/phase-3/price.jsonl), [log test](../proof/phase-3/tests.txt) | Đạt |
| AC-P3-05 | Kho Quán tick 0 khớp đúng file. Vòng `day` bàn giao cùng tick, pause Shop giữ độ tươi, Ngày sau cấp ID mới. Kiểm hàm HUD nhận ra hàng ươn và lượng khả dụng từ snapshot mẫu. | [JSONL Quán](../proof/phase-3/quan.jsonl), [JSONL vòng ngày](../proof/phase-3/day.jsonl), [log HUD](../proof/phase-3/hud.txt) | Đạt |
| AC-P3-06 | Smoke CLI qua file và `day`, kho đếm trả mã 2, 134/134 test đạt. | [Lệnh và kết quả](../proof/phase-3/integration.txt), [log test](../proof/phase-3/tests.txt) | Đạt |

Các test hồi quy kiểm luật v1.1 theo loại nguyên liệu dùng fixture đã chuyển sang schema mới khi gọi CLI v1.2. Test riêng kiểm chính xác ID, `fresh`, thứ tự event và file. Các ca v1.1 dùng trực tiếp lớp sim giữ tuning v1.1. Xem [CHANGELOG](../../CHANGELOG.md) để đổi fixture.
