# Checklist kiểm chứng UI Phase 2

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Menu, DayIntro | Chọn **Chơi**, xem kế hoạch Ngày 1/5, thử bỏ qua bằng phím và chờ Ngày 2 tự bắt đầu sau 4 giây | Đạt trên snapshot mẫu |
| Gather | Kiểm camera, 6 nút rau, cá kèo, cá sấu, vạch 10 m, cảnh báo tím, oxy thấp và cạn, giỏ và mục tiêu nguyên liệu | Đạt trên snapshot mẫu |
| EveningIntro | Xem nguyên liệu nhập kho, món đủ nguyên liệu và kho rỗng khi ngất ở Ngày 3 | Đạt trên snapshot mẫu |
| Quan | Kiểm 2 bếp, 4 bàn, trạng thái nấu và bưng, cảnh báo kiên nhẫn thấp, mốc boa 50%, kho trừ giữ chỗ và thực đơn theo ngày | Đạt trên snapshot mẫu |
| DayResult, Shop | Đối chiếu số khách, tiền món và boa. Mua bình oxy Ngày 1, áo phao Ngày 4, kiểm hiệu lực từ hôm sau | Đạt trên snapshot mẫu |
| Pause, chuyển pha | Tạm dừng cả ba pha. Kiểm ảnh Canvas và đồng hồ Shop đứng yên, giữ E qua pha không tạo thao tác mới | Đạt trên snapshot mẫu |
| Summary | Hoàn thành 5 ngày, đối chiếu doanh thu, tiền còn, uy tín, điểm và món bán chạy nhất. Thử chơi lại và về menu | Đạt trên snapshot mẫu |
| 1280×720 | Kiểm chữ HUD và nút từ 18 px, không tràn màn ở các trạng thái đo. Đếm lần vẽ Canvas trong 1,4 giây mỗi cảnh | Đạt trên Chrome headless, Gather 59,9 FPS và Quan 60,2 FPS |
| Phase 1 | Chạy suite và kiểm chuyển kho trên UI live | 45/45 test đạt, chuyển đúng kho |
| Live/headless v1.1 | Chạy lại khi contract chính thức và bộ mô phỏng day được tích hợp | Chờ tích hợp, checkout dùng v1.0 |

[Xem lệnh chạy và chi tiết kiểm thử](../proof/phase-2/client-ui.md).
# Ma trận truy vết Phase 2 — Test Contract v1.1

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Chuyển kho gather → quán | Seed 42, xuất kho khi cập bến, đối chiếu stock ở snapshot quán tick 0 | [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt trên 751da31 và 2090b6e. Chờ kiểm lại trên bản tích hợp. |
| Mua oxy đúng giá, áp dụng từ Ngày kế | Chạy `day --days 2`, mua với đúng 200 tiền và kiểm tra oxy đầu Ngày 2 | [Test day/Shop](../../tests/test_qa_phase2.py) | CLI tại `e7afc1e` trả mã 2 với `--days 2`. Luật Shop chưa được kiểm chứng. |
| Vòng ngày và kế hoạch D1–D5 | Smoke `day --days 1`, kiểm tra chuyển pha, kế hoạch và `days_completed` khi Shop đóng | — | Chưa chạy trên v1.1. |
| Pause | Kiểm tra đồng hồ và bộ đếm đứng yên khi pause; gameplay tiếp tục ngay ở bước resume | [Test pause](../../tests/test_qa_phase2.py) | Baseline tại `cb04f1e`: CLI trả mã 2 vì frame 0 có trường `pause` chưa được hỗ trợ. Chưa kiểm chứng hành vi pause/resume. |
| Số liệu chuẩn, cá, Cá Sấu | Đối chiếu manifest và chạy fixture biên cho cá, Cá Sấu | — | Chưa chạy trên v1.1. |
| Regression Phase 1 | Chạy toàn bộ suite có sẵn trên nhánh quán, gồm smoke Phase 1 và hai ca QA Phase 1 | [Bằng chứng regression](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | 48/48 đạt trên `2090b6e`. Chờ chạy lại trên bản tích hợp Phase 2. |
| Cá Sấu — Chạm làm ngất ở 1 Máu | Kiểm tra `monster_hit → faint → gather_end` trong cùng tick, hai lượt rơi đồ theo LIFO và kho rỗng | [Test Cá Sấu](../../tests/test_qa_phase2.py) | Baseline tại `093237e` trả mã 2 vì chưa hỗ trợ `gather.monsters`. Chưa kiểm chứng luật va chạm và ngất. |
| Quán mở rộng — 2 bếp, 4 bàn và 6 món | Chạy suite quán, gồm snapshot, món mới, thứ tự nhận đơn, lọc món theo kế hoạch và dọn ca | [Kết quả trên nhánh quán](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | 12/12 ca quán đạt trên `2090b6e`. Chờ kiểm lại trên bản tích hợp. |
