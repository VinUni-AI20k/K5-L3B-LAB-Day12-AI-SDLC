# Ma trận truy vết Phase 3 — Test Contract v1.2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Ngưỡng ươn trong giỏ | Cá thể ở fresh 30 lúc dựng fixture. Chạy hai tick, kiểm spoiled chỉ phát ở tick 1 và hàng vẫn chiếm ô | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline `8739a9f` trả mã 2 khi đọc `gather.hold` dạng cá thể. Chưa chạy tới bước hao tươi. |
| Bàn giao kho cá thể qua file | So id, kind và fresh giữa gather_end, file xuất và snapshot quán tick 0 | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline `8739a9f` trả mã 2 khi đọc `gather.hold` dạng cá thể. Luồng dừng trước khi xuất kho. |
| Từ chối kho đếm | Nạp `{"items":{"ca_loc":1}}` vào quán. Với v1.2, kiểm mã thoát 2 và không tạo JSONL | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline v1.1 tại `8739a9f` nhận kho đếm và thoát mã 0. Chờ kiểm lại khi bật v1.2. |
| Giữ lại nguyên liệu và chốt giá | Nguyên liệu giữ chỗ vừa ươn ở tick 1. Kiểm chọn lại cá thể tươi nhất trước khi nấu và chốt giá 53 | [Test QA Phase 3](../../tests/test_qa_phase3.py) | Baseline v1.1 trả mã 2 với lỗi `items phải là object`. Chưa chạy tới bước giữ lại nguyên liệu và chốt giá. |
| Hồi quy gather và suite trên main | Chạy suite gather freshness và toàn bộ test trên main | [Bằng chứng QA](../proof/phase-3/qa.md) | Tại `355ce0b`: gather freshness 3/3, toàn bộ suite 54/57. Ba lỗi Phase 2 vẫn còn. |

## Tác động lên regression P1–P2

- Khi bật v1.2, đổi fixture giỏ từ mảng mã nguyên liệu sang mảng cá thể. Cập nhật assertions cho lost, stock và file kho theo schema mới.
- Giữ kiểm tra LIFO, ngất, kho rỗng và không ghi đè file khi dừng do giới hạn tick.
- Kiểm lại riêng hai lỗi Phase 2 còn mở là CLI thiếu `--days` và parser chưa nhận `pause`.
# Checklist kiểm chứng UI Phase 3

| Hạng mục | Kiểm chứng | Kết quả |
|---|---|---|
| Giỏ có hàng ươn | Duyệt Ngày 1 bằng E, Space. Ô cá linh 28,5% vẫn chiếm chỗ và có gạch chéo. Kho và mục tiêu dùng số còn tươi. | Đạt trên snapshot mẫu |
| Cảnh báo và mất đồ | Kiểm toast hàng ươn, nháy viền giỏ, tên món rơi theo LIFO khi bị quái đánh và khi ngất. | Đạt trên snapshot mẫu |
| Bàn giao kho | Đối chiếu 1 cá linh ươn, trung bình cá linh tươi 80,08% và bông súng 56,62%. Lọc món theo nguyên liệu tươi. | Đạt trên snapshot mẫu |
| Giữ chỗ và hàng ươn | Khi bông súng giữ chỗ chuyển từ 30% sang 29,75%, kho hiện một bông ươn, nhả giữ chỗ và bàn chuyển sang **Hết hàng tươi!**. Gỏi bông súng đổi sang thiếu kho. | Đạt trên snapshot mẫu |
| Giá chốt và tổng kết | Đối chiếu 103k trên bếp, tay và bàn. Giá bị khóa theo snapshot. Hoàn thành cả 5 ngày và xem tổng kết. | Đạt trên snapshot mẫu |
| Shop và Pause | Kho dư giữ màu và số lẻ, có ghi chú giữ nguyên độ tươi. Khi Pause, ảnh Canvas và giá trị kho đứng yên. | Đạt trên snapshot mẫu |
| 1280×720 | Kiểm cỡ chữ từ 18 px và bố cục Giỏ, chuyển ca, Quán, Shop, tổng kết và Quán độc lập. Đo Canvas khoảng 60 FPS mỗi cảnh. | Đạt trên Chrome headless |
| Đọc kho đếm | Chạy lại bản xem Phase 1, Phase 2 và bàn giao qua live với sim v1.1. | Đạt |
| Headless của checkout | 51/54 test đạt. Ba ca lỗi được tái hiện cùng kết quả ở commit nền `881c4c4`. | Kết quả giữ nguyên |
| Live/headless v1.2 | Chạy lại khi sim v1.2 được tích hợp. | Chờ tích hợp |

[Bằng chứng, lệnh chạy và đoạn CHANGELOG](../proof/phase-3/client-ui.md).
