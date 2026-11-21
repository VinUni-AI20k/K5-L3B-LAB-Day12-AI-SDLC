# Ma trận kiểm chứng Phase 2

Các nhãn dưới đây là nhóm yêu cầu nội bộ của TV1 theo TICKET-02, mục 1.1, 1.2 và 4. Kết quả áp dụng cho cây làm việc đã chạy test, chờ commit bàn giao.

| Yêu cầu | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| Cá Sấu patrol/chase/recoil, ngưỡng độ sâu và biên | Fixture headless, so snapshot theo tick | [TV1](../proof/phase-2/tv1-monsters.md) | Đạt các ca đã liệt kê |
| Chạm, bất tử, mất hàng LIFO và ngất | So thứ tự event, HP, lost và file kho | [TV1](../proof/phase-2/tv1-monsters.md) | Đạt |
| M2 từ ngày 3 | Khởi tạo GatherSim với day=1,2,3 | [TV1](../proof/phase-2/tv1-monsters.md) | Đạt ở giao diện sim |
| Regression Phase 1 | python -m unittest discover -s tests | [TV1](../proof/phase-2/tv1-monsters.md) | 70/70 test đạt trên workspace |
| Day, Shop và nâng cấp có hiệu lực ngày sau | Chạy CLI day sau tích hợp TV4 | Chưa có | Chưa kiểm chứng |
| Ngất vẫn mở quán với kho rỗng | Chạy day sau tích hợp TV4 | Hiện đã kiểm file kho rỗng ở gather độc lập | Chưa kiểm chứng chuyển pha |
| Cá bơi/sinh, 6 món, 2 bếp/4 bàn, HUD và hiệu năng | Chủ lát bổ sung sau bàn giao | Chưa có | Chờ tích hợp |

## Đánh giá

TV1 hoàn thành logic quái và các ca sinh tồn trong phạm vi nêu trên. Cần ghép số ngày, tuning nâng cấp, chuyển pha và HUD trước khi kết luận Phase 2 đạt DoD.
