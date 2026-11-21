# Ma trận truy vết Phase 2 — Test Contract v1.1

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Chuyển kho gather → quán | Seed 42, xuất kho khi cập bến, đối chiếu stock ở snapshot quán tick 0 | [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt trên main tại 8c1d93c với nguyên liệu Phase 1. |
| Bàn giao nguyên liệu mới — `ca_keo`, `keo_neo` | Kiểm tra fixture giỏ gather rồi kiểm tra riêng quán nạp kho | [Bằng chứng](../proof/phase-2/integration.md) | Quán nạp trực tiếp đạt tại 9f4c078. Smoke hai tiến trình tại 8c1d93c bị chặn ở gather.hold, mã 2. |
| Mua oxy đúng giá, áp dụng từ Ngày kế | Chạy `day --days 2`, mua với đúng 200 tiền và kiểm tra oxy đầu Ngày 2 | [Test day/Shop](../../tests/test_qa_phase2.py) | Tại 8c1d93c, CLI từ chối --days 2. Chưa kiểm được luật mua và áp dụng nâng cấp. |
| Vòng ngày và kế hoạch D1–D5 | Smoke `day --days 1`, kiểm tra chuyển pha, kế hoạch và `days_completed` khi Shop đóng | — | Chưa chạy trên v1.1. |
| Pause | Kiểm tra đồng hồ và bộ đếm đứng yên khi pause; gameplay tiếp tục ngay ở bước resume | [Test pause](../../tests/test_qa_phase2.py) | Tại 8c1d93c, parser từ chối pause tại frame 0. Chưa kiểm được hành vi pause/resume. |
| Số liệu chuẩn, cá, Cá Sấu | Đối chiếu manifest và chạy fixture biên cho cá, Cá Sấu | — | Chưa chạy trên v1.1. |
| Regression Phase 1 | Chạy toàn bộ suite có sẵn trên nhánh quán, gồm smoke Phase 1 và hai ca QA Phase 1 | [Bằng chứng regression](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | Suite tích hợp tại 8c1d93c đạt 51/54. Ba lỗi xác thực đầu vào được ghi trong bằng chứng tích hợp. |
| Cá Sấu — Chạm làm ngất ở 1 Máu | Kiểm tra `monster_hit → faint → gather_end` trong cùng tick, hai lượt rơi đồ theo LIFO và kho rỗng | [Test Cá Sấu](../../tests/test_qa_phase2.py) | 	Ca gây ngất ở 1 Máu đạt tại 8c1d93c. Ca không gây ngất bị chặn khi kiểm tra gather.hold. |
| Quán mở rộng — 2 bếp, 4 bàn và 6 món | Chạy suite quán, gồm snapshot, món mới, thứ tự nhận đơn, lọc món theo kế hoạch và dọn ca | [Kết quả trên nhánh quán](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | 12/12 ca quán đạt trên main tại 8c1d93c. |