# vuhieuvh — phản tư cá nhân (≤ 200 từ)

## Phase 1
- **Tôi đã làm (kèm link commit):**
  - Khởi tạo khung ma trận kiểm thử Phase 1 ([docs/verification/phase-1.md](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/verification/phase-1.md)).
  - Chuẩn bị sẵn bộ kịch bản test handoff kho hai tiến trình ([dock.json](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-1/dock.json), [dock-inputs.json](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-1/dock-inputs.json)).
  - Chạy kiểm thử xác thực độc lập cho Lát 1 (bơi, oxy, ngạt, ngất, giỏ) và Lát 2 (hái rau, bắt cá, hồi chiêu, cập bến xuất kho) với 45/45 test toàn dự án đạt ([lat1_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-1/lat1_test.log), [lat2_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-1/lat2_test.log)).
- **Tôi đã review (kèm link):**
  - Review commit `e07352e` của TV1 (`feat(gather): finalize team, contracts and implement Lat 1`): đạt 5/5 unit test.
  - Review commit `38e08b2` & `fb5a133` của TV2 (`thangdktd`): xác nhận Lát 2 hái/bắt cá hoạt động chính xác và handoff file kho thành công.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu chưa cấu hình tương thích lệnh `python3` trên Windows dẫn đến mã lỗi 9009; tôi phát hiện qua log unittest và khắc phục.
- **Điều tôi học được:**
  - Tầm quan trọng của việc kiểm thử liên tục từng lát cắt (Continuous Testing) giúp phát hiện xung đột sớm và giữ nhánh chính luôn ổn định.

## Phase 2
- **Tôi đã làm (kèm link commit):**
  - Khởi tạo ma trận kiểm chứng Phase 2 với 12 tiêu chí AC-P2-01 đến AC-P2-12 ([docs/verification/phase-2.md](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/verification/phase-2.md)).
  - Nâng cấp giao diện trực quan Cá Sấu giải phẫu chi tiết (thân vảy, mõm, răng nanh, gờ mắt, chân màng bơi, đuôi) và hiệu ứng vòng tuần tra/truy đuổi trên [chonoi/web/index.html](file:///e:/ai_thuc_chien/day_12_thuc_hanh/chonoi/web/index.html).
  - Tích hợp và chạy kiểm thử toàn bộ 5 lát cắt của cả nhóm: 78/78 tests toàn dự án đạt 100% ([p2_full_test.log](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/p2_full_test.log)), nghiệm thu tính tất định vòng ngày `--mode day` ([day_smoke.jsonl](file:///e:/ai_thuc_chien/day_12_thuc_hanh/docs/proof/phase-2/day_smoke.jsonl)).
- **Tôi đã review (kèm link):**
  - Review commit `d24284f` của TV1 (Cá Sấu M1/M2: patrol, chase, hit, recoil, LIFO hold loss).
  - Review commit `9d7d6a1` của TV2 (Đàn cá di chuyển, va chạm biên đổi hướng, spawn định kỳ).
  - Review commit `1cfdc46` của TV3 (Lọc thực đơn Quán theo `day_plan`).
  - Review commit `c82f599` của TV4 (Vòng đời `--mode day`, shop nâng cấp, pause).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI khai báo trùng biến `const p` trong hàm vẽ canvas gây ra lỗi màn hình đen; tôi dùng `node -c` và DevTools để bắt lỗi cú pháp và sửa ngay.
- **Điều tôi học được:**
  - Đảm bảo tách biệt rõ ràng giữa logic mô phỏng contract và tầng trình diễn giao diện Web giúp game vừa sinh động vừa đảm bảo tuyệt đối tính tất định headless.
