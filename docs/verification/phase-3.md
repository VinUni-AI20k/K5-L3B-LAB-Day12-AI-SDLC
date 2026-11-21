# Ma trận truy vết Phase 3

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-04 · TV4 | Kiểm đúng ID tiêu, thứ tự payload, giá sát biên floor và boa. Chạy ca hao tươi đủ 60 bước trước khi nấu. | [Kiểm chứng TV4](../proof/phase-3/tv4-bep-vong-ngay.md) | Đạt khi dùng độ tươi đầu vào chính xác. Ca hao tươi 60 bước trên bản ghép cho giá 29 thay vì 30. |
| AC-P3-05 · TV1 + TV4 + TV5 | Chạy day hai ngày với giỏ fixture, so sự kiện bàn giao với stock đầu quán, kiểm ID ngày sau và độ tươi trong Shop/pause. | [Kiểm chứng TV4](../proof/phase-3/tv4-bep-vong-ngay.md) | Day đạt trên bản ghép tạm. Bàn giao qua file v1.2 chờ kiểm trên bản tích hợp. |
| AC-P3-06 · phần regression TV4 | Chạy bộ test trên nhánh TV4 với manifest v1.1. | [Kiểm chứng TV4](../proof/phase-3/tv4-bep-vong-ngay.md) | 97 đạt, 1 test day cá thể bỏ qua và đã đạt khi chạy riêng trên bản ghép tạm. |

Ma trận hiện ghi kết quả TV4 trên cây làm việc và bản ghép tạm. TV1 và TV5 bổ sung kết quả của các lát còn lại trên commit bàn giao.
