# Ma trận truy vết Phase 2 — Test Contract v1.1

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Chuyển kho gather → quán | Seed 42, xuất kho khi cập bến, đối chiếu stock ở snapshot quán tick 0 | [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt trên 751da31 và 2090b6e. Chờ kiểm lại trên bản tích hợp. |
| Mua oxy đúng giá, áp dụng từ Ngày kế | Chạy `day --days 2`, mua với đúng 200 tiền và kiểm tra oxy đầu Ngày 2 | [Test day/Shop](../../tests/test_qa_phase2.py) | CLI tại `e7afc1e` trả mã 2 với `--days 2`. Luật Shop chưa được kiểm chứng. |
| Vòng ngày và kế hoạch D1–D5 | Smoke `day --days 1`, kiểm tra chuyển pha, kế hoạch và `days_completed` khi Shop đóng | — | Chưa chạy trên v1.1. |
| Pause | Kiểm tra đồng hồ và bộ đếm đứng yên khi pause; gameplay tiếp tục ngay ở bước resume | [Test pause](../../tests/test_qa_phase2.py) | Baseline tại `cb04f1e`: CLI trả mã 2 vì frame 0 có trường `pause` chưa được hỗ trợ. Chưa kiểm chứng hành vi pause/resume. |
| Số liệu chuẩn, cá, Cá Sấu | Đối chiếu manifest và chạy fixture biên cho cá, Cá Sấu | — | Chưa chạy trên v1.1. |
| Regression Phase 1 | Chạy lại suite, ghi lý do cho từng assertion cần đổi theo v1.1 | — | Chưa chạy trên bản tích hợp v1.1. |
| Cá Sấu — Chạm làm ngất ở 1 Máu | Kiểm tra `monster_hit → faint → gather_end` trong cùng tick, hai lượt rơi đồ theo LIFO và kho rỗng | [Test Cá Sấu](../../tests/test_qa_phase2.py) | Baseline tại `093237e` trả mã 2 vì chưa hỗ trợ `gather.monsters`. Chưa kiểm chứng luật va chạm và ngất. |
| Quán mở rộng — 2 bếp, 4 bàn và 6 món | Chạy suite quán, gồm snapshot, món mới, thứ tự nhận đơn, lọc món theo kế hoạch và dọn ca | [Kết quả trên nhánh quán](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | 12/12 ca quán đạt trên `2090b6e`. Chờ kiểm lại trên bản tích hợp. |