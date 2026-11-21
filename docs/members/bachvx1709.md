# bachvx1709 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Chịu trách nhiệm module `client/ui` và vai trò QA Lead, Release cho Phase 1.
  - Viết bộ unit test `tests/test_phase1_gameplay.py` và chạy smoke test hộp đen theo Test Contract v1.0.
  - Lập ma trận kiểm chứng `docs/verification/phase-1.md` và thu thập toàn bộ log/bằng chứng thật trong `docs/proof/phase-1/`.
  - Tích hợp 3 tính năng sáng tạo đặc sắc cho nhóm: Hệ thống âm thanh Web Audio API, Hộp thoại Nam Bộ tương tác, và Hiệu ứng đồ họa sông nước/khói bếp trên Canvas (commit `1d4943e`).
- **Tôi đã review (kèm link):**
  - Review chéo logic mô phỏng `chonoi/sim/gather.py` và `chonoi/sim/quan.py`, bảo đảm tuân thủ nghiêm ngặt Test Contract v1.0 và tính xác định (determinism).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI viết test giữ phím `interact=True` liên tục làm mất cạnh lên (rising edge), khiến lệnh phục vụ bàn không nhận. Tôi phát hiện qua assertion failure của unittest và sửa nhả phím `interact=False`.
- **Điều tôi học được:**
  - Hiểu sâu về kiến trúc tick-based deterministic simulation và quy trình cộng tác phân tách rõ ràng giữa mô phỏng headless và tầng giao diện người dùng.

## Phase 2

- **Tôi đã làm:** thiết kế lại `chonoi/web/index.html` (menu, DayIntro, HUD hai ca, EveningIntro, DayResult, Shop, Summary, pause, Cài đặt âm thanh); `chonoi/live_day.py` bọc DaySim thật của TV4 thành các màn UI; thêm Chợ Chú Sáu, thời tiết, chuyện Má Tư, khách quen; `tools/qa_p2.py` (7 checkpoint), `tests/test_live_day.py`, ma trận `docs/verification/phase-2.md`, đo FPS.
- **Tôi đã review:** đọc DaySim/runner của TV4 (PR #11) để gộp `chonoi/live.py` và đối chiếu event chuyển pha; chạy lại fixture day/pause/ngất của TV1, TV4 bằng CLI.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI để tick của pha con đè tick tổng trong snapshot, client tưởng chơi lại nên nhảy màn — phát hiện khi chơi thử trên trình duyệt. AI cũng viết file inputs có hai frame cùng tick khiến CLI trả mã 2 — phát hiện nhờ QA script báo FAIL rồi đọc stderr.
- **Điều tôi học được:** làm UI theo hợp đồng snapshot giúp làm song song; nhưng phải chuyển sang đúng sim của headless sớm để không kiểm chứng trên một bản “gần giống”.

## Phase 3

- **Tôi đã làm:** HUD độ tươi (thanh tươi từng ô, hàng ươn, đồng hồ ươn, giá dự kiến, Má Tư chấm hàng), đồ họa mới, hướng dẫn Ngày 1, đóng quán sớm; `live_day` đọc kho cá thể, Chợ Chú Sáu theo v1.2; `tools/qa_p3.py` 8 checkpoint; đổi test TV5 theo version; `docs/verification/phase-3.md`.
- **Tôi đã review:** chạy lại bằng CLI các ca của TV1–TV4 (ngưỡng 30, giữ lại khi ươn, giá 50.25 → 30, id xuyên ngày) trên bản bật 1.2; đối chiếu log để lập danh sách 18 test còn dùng kho đếm theo chủ lát.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI so event JSONL với file kho bằng `==` nên báo lệch giả — đọc lại ticket về dung sai ±0.01 thì sửa. AI cũng xóa nhầm dòng chặn lệnh Chợ khi thêm tính năng mới; test bắt được.
- **Điều tôi học được:** khi đổi hợp đồng dữ liệu, chạy toàn suite trên version mới sớm quan trọng hơn để từng lát tự xanh trên version cũ.
