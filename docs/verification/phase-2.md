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
