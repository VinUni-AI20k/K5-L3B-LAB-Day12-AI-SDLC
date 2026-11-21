# Ma trận truy vết Phase 2 (TV5 - QA Lead)

| AC | Yêu cầu kiểm chứng | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| **AC-P2-01** | Manifest v1.1 & Cấu hình | Kiểm tra `contract_version: "1.1"`, 6 nguyên liệu, 6 món, cấu hình Shop, `day_plan` D1–D5 | [game.contract.json](file:///e:/ai_thuc_chien/day_12_thuc_hanh/game.contract.json) | **ĐẠT (PASS)** |
| **AC-P2-02** | Lát 1: Cá Sấu M1/M2 tuần tra & rượt đuổi | Quái M1 (từ D1), M2 (từ D3). Patrol 1.0 m/s; phát hiện người chơi khi $d \ge 10$ và khoảng cách $\le 10$m $\rightarrow$ chase 3.0 m/s; thoát khi cách $>16$m hoặc $d < 10$ | [p2_monsters_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_monsters_test.log) | **ĐẠT (PASS - 5/5 tests)** |
| **AC-P2-03** | Lát 1: Cá Sấu tấn công, recoil & rớt đồ | Hit khi cách $\le 1.5$m, người chơi $d \ge 10$, hết bất tử: giảm 1 HP, rớt `floor(hold/2)` theo LIFO, bất tử 90 tick, quái recoil 60 tick (lùi 2.0 m/s) | [p2_monsters_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_monsters_test.log) | **ĐẠT (PASS)** |
| **AC-P2-04** | Lát 2: Đàn cá bơi, đổi hướng & sinh thêm | Cá bơi 1.5 m/s, turn 120 tick, spawn mỗi 360 tick (8 đàn đầu, max 12 đàn, tỉ lệ 40% linh / 30% lóc / 30% kèo) | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS - 9/9 tests)** |
| **AC-P2-05** | Lát 2: Nội dung mới (cá kèo, kèo nèo N5/N6) | Bắt cá kèo (`ca_keo`), hái kèo nèo (`keo_neo`) tại các điểm nút N5, N6 | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS)** |
| **AC-P2-06** | Lát 3: Quán mở rộng 2 bếp B1/B2 & 4 bàn T1–T4 | Mô phỏng Quán với 2 bếp độc lập, 4 bàn nhận khách; kiểm tra điều phối đơn chờ | [tv3-quan.md](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/tv3-quan.md) | **ĐẠT (PASS)** |
| **AC-P2-07** | Lát 3: Thực đơn 6 món & lọc theo `day_plan` | 6 món đúng công thức, khách chỉ gọi các món nằm trong kế hoạch ngày (`dishes` của D1–D5) | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS - 2/2 tests)** |
| **AC-P2-08** | Lát 4: Vòng đời chế độ Ngày (`--mode day`) | Luồng pha: `DayIntro → gather → EveningIntro → quan → DayResult → Shop` qua các ngày D1–D5 | [day_smoke.jsonl](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/day_smoke.jsonl) | **ĐẠT (PASS - 10/10 tests)** |
| **AC-P2-09** | Lát 4: Shop & Nâng cấp sang ngày hôm sau | Shop 600 tick, mua nâng cấp oxy/máu; xác nhận chỉ có hiệu lực từ Ngày tiếp theo | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS)** |
| **AC-P2-10** | Lát 4: Cơ chế Tạm dừng (`pause`) | Khi pause: tick ngoài tăng nhưng `sim_tick`, `phase_tick` và các bộ đếm không chạy | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS)** |
| **AC-P2-11** | Kiểm tra hồi quy toàn dự án | Chạy lại toàn bộ test suite dự án kết hợp tất cả các thành viên | [p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log) | **ĐẠT (PASS - 78/78 tests)** |
| **AC-P2-12** | HUD trực quan v1.1 | Hiển thị Cá Sấu chi tiết giải phẫu dưới nước, vòng cảnh báo và trạng thái chase/recoil trên trình duyệt | [chonoi/web/index.html](file:///e:/ai_thuc_chien/day_12_thuc_hanh/chonoi/web/index.html) | **ĐẠT (PASS - Đã nâng cấp HUD Cá Sấu chi tiết)** |

## Đánh giá ngắn Phase 2
- **Yêu cầu đã đạt:**
  - Toàn bộ 5 lát cắt của Phase 2 từ TV1, TV2, TV3, TV4 đã được tích hợp đầy đủ và kiểm thử nghiệm thu.
  - Tổng cộng 78/78 unit & integration test đều PASS mà không có bất kỳ lỗi nào.
  - Chạy headless chế độ `--mode day` đảm bảo tính tất định từng byte (`day_smoke.jsonl`).
  - Giao diện trực quan HUD cá sấu được trau chuốt tỉ mỉ (thân, mõm, mắt, gai lưng, chân màng bơi, đuôi).
- **Yêu cầu tồn đọng / lưu ý:** Sẵn sàng cho TV1 merge vào `origin/main` và gắn tag `phase-2`.
