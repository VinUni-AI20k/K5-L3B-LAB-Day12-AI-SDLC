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
