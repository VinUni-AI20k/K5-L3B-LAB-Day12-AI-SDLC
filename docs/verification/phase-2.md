# Ma trận truy vết Phase 2 — Test Contract v1.1

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Chuyển kho gather → quán | Seed 42, xuất kho khi cập bến, đối chiếu stock ở snapshot quán tick 0 | [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt trên baseline `751da31`. Chờ chạy lại trên bản tích hợp v1.1. |
| Mua oxy đúng giá, áp dụng từ Ngày kế | Chạy `day --days 2`, mua với đúng 200 tiền và kiểm tra oxy đầu Ngày 2 | [Test day/Shop](../../tests/test_qa_phase2.py) | CLI tại `e7afc1e` trả mã 2 với `--days 2`. Luật Shop chưa được kiểm chứng. |
| Vòng ngày và kế hoạch D1–D5 | Smoke `day --days 1`, kiểm tra chuyển pha, kế hoạch và `days_completed` khi Shop đóng | — | Chưa chạy trên v1.1. |
| Pause | So snapshot trước và trong pause ở gather, quán và Shop. Kiểm tra gameplay tiếp tục ở bước resume | — | Chưa chạy trên v1.1. |
| Số liệu chuẩn, cá, Cá Sấu và quán mở rộng | Đối chiếu manifest và chạy fixture biên cho cá, Cá Sấu, 2 bếp và 4 bàn | — | Chưa chạy trên v1.1. |
| Regression Phase 1 | Chạy lại suite, ghi lý do cho từng assertion cần đổi theo v1.1 | — | Chưa chạy trên bản tích hợp v1.1. |