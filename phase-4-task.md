# Bảng công việc Phase 4 (2:30–3:00 · Test Contract v1.3 — Phát hành `v1.0.0`)

> **Lưu ý quan trọng:** Chỉ bắt đầu thực hiện bảng này **sau khi đã gắn tag `phase-3`**. Gameplay, tuning, kho và JSONL giữ nguyên theo `v1.2`; Phase 4 tập trung vào **Benchmark (`bench_cmd`)**, **Soak (`soak_cmd`)**, **Cảnh báo & Tương phản cao**, **Đóng gói**, **Retro tổng kết**, **Tag `phase-4` + GitHub Release `v1.0.0`** và **Demo**.

**Quy ước:** đợt 1 làm ngay lúc 2:30, đợt 3 chốt & phát hành trước 3:00.

**Danh sách thành viên:** Huy (`huyvu-03` — M1) · Quang (`QuangNEU` — M2) · Cao (`ththanh8888` — M3) · Minh (`NhMinh-2610` — M4) · Thanh (`thanhvu101` — M5) · An (`K0heii` — M6, kiêm PO/Integrator/Release).

| Đợt | Mã task | Người | Module | Việc cần làm | Chờ ai / task nào | Ai chờ mình |
|---|---|---|---|---|---|---|
| **1** (2:30–2:45, làm song song) | M6.1 | An (M6) | M6 | Nâng `game.contract.json` lên `contract_version: "1.3"`, khai báo `bench_cmd` và `soak_cmd` ở gốc manifest; tạo `docs/plan/phase-4.md` | Tag `phase-3` | M2.1, M5.1, M6.2 |
| 1 | M5.1 | Thanh (M5) | M5 | Code **`bench_cmd`** (`--seed 42 --duration 30 --out bench.json`): cảnh lặn lõi (độ tươi, cá bơi, Cá Sấu, Út Sen đứng yên ở bến, 1280×720, làm nóng 3 s + đo 30 s) xuất đủ 5 trường `avg_fps, p1_low_fps, frames, measured_s, load_ms` | M6.1 | M5.3, M6.2 |
| 1 | M5.2 | Thanh (M5) | M5 | Bổ sung **3 cảnh báo dễ nhận biết** bằng chữ/biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) + **chế độ tương phản cao** (High Contrast toggle) trên `chonoi/web/` | Không | M5.3 |
| 1 | M2.1 | Quang (M2) | M2 | Code **`soak_cmd`** (`--seed 7 --days 10 --out soak.json`): chạy 10 Ngày liên tục trong 1 tiến trình headless (D1–D5 lặp cho D6–D10, tiền/earned/uy tín/cấp/id cá thể xuyên suốt) xuất `days, days_completed, crashes, results[], duration_s` | M6.1 | M4.1, M6.2 |
| 1 | M4.1 | Minh (M4) | M4 | Hỗ trợ Quang hoàn thiện script bot tất định cho `soak_cmd` (đảm bảo `days_completed == days`, `crashes == 0`, lặp lại cho kết quả gameplay giống nhau) + hoàn thiện Mở rộng (nếu chọn `leaderboard`) | M2.1 | M6.2 |
| 1 | M1.1 | Huy (M1) | M1 | **Đóng gói & thử clone sạch**: clone repo ra thư mục trống, chạy bản có giao diện theo `README.md` trong ≤ 3 lệnh, kiểm tra yêu cầu môi trường, điều khiển, lệnh test/headless/bench/soak, đóng gói artifact cho GitHub Release `v1.0.0` | Không | M6.3 |
| 1 | M3.1 | Cao (M3) | M3 | Chạy toàn bộ **regression P1–P3** + test `bench_cmd` / `soak_cmd`, tổng hợp log bằng chứng vào `docs/proof/phase-4/` | M2.1, M5.1 | M6.2 |
| **2** (2:45–2:55, Retro & Kiểm chứng) | M5.3 | Thanh (M5) | M5 | Chạy thật `bench_cmd --seed 42 --duration 30 --out docs/proof/phase-4/bench.json`, chơi thử cả 3 cảnh báo ở chế độ tương phản cao & chụp ảnh bằng chứng; chuẩn bị kịch bản **Demo ≤ 5 phút** | M5.1, M5.2 | M6.2 |
| 2 | M6.2 | An (M6, PO) | M6 | Chạy `soak_cmd --seed 7 --days 10 --out docs/proof/phase-4/soak.json` (kiểm tính lặp), rà `README.md` (đủ lệnh chạy ≤ 3 bước, test, headless, bench, soak, mục Mở rộng & Sáng tạo), rà `CREDITS.md` & `LICENSE`, điền `docs/verification/phase-4.md` | M1.1, M3.1, M4.1, M5.3 | M6.3 |
| 2 | ALL-R | Cả 6 người | M1–M6 | **Retro tổng kết (5 phút)** vào `docs/retro.md` (rà lại hành động đã chốt ở P2, nêu 1 lỗi AI mắc & cách xác minh); mỗi người chốt `docs/members/<handle>.md` (≤ 200 từ, dẫn commit) & cập nhật `docs/ai-usage-log.md` | Không | M6.3 |
| **3** (2:55–3:00, Phát hành) | M6.3 | An (M6, Release) | M6 | Hoàn thiện `CHANGELOG.md` đủ 4 phase, viết Release Notes (điểm mới, cách chạy, giới hạn đã biết), chạy `check_team.py` + toàn bộ `unittest`, **đẩy tag `phase-4` và công bố GitHub Release `v1.0.0`** (đính kèm bản đóng gói) trên cùng commit `main` trước **3:00** | M1.1, M6.2, ALL-R | Demo sau 3:00 |

## Mở rộng (tùy chọn — nếu nhóm chưa đủ 2 mục Mở rộng bắt buộc cho 6 người)
- **`leaderboard` (Bảng xếp hạng cục bộ)**: Minh (M4) — lưu top 10 lượt chuẩn 5 Ngày, `<run_cmd> --export-leaderboard`, cờ `--leaderboard` + `--player-name` trong `day` (thiếu 1 cờ hoặc sai mode → mã `2`), không đổi JSONL, `soak` không ghi xếp hạng.
- **Phụ đề SFX**: Thanh (M5) — hiện phụ đề cho hiệu ứng âm thanh khi tắt tiếng.

## Checklist Demo sau 3:00 (trực tiếp hoặc video `.mp4` < 5 phút — Thanh & An dẫn chính)
1. Chơi trọn 1 Ngày từ **Lặn & Hái → Mở Quán → đóng Shop** (có bật thử 3 cảnh báo & chế độ tương phản cao).
2. Chạy lệnh test (`unittest`) cho thấy toàn bộ kết quả đạt.
3. Mở repo chung chỉ ra bằng chứng chia việc, phối hợp và đóng góp commit của đủ 6 người (`TEAM.md`, git log, `docs/members/`).
4. Mở ma trận truy vết (`docs/verification/phase-1..4.md`) và chỉ ra bằng chứng thật trong `docs/proof/`.

## Ba điểm dễ nghẽn

1. **`bench_cmd` chạy trong môi trường không có trình duyệt tự động hoặc thiếu 1 trong 5 trường `bench.json`**: Thanh (M5) cần chạy thử thật và kiểm định JSON output đúng đủ 5 khóa (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`) trước **2:45**.
2. **`soak_cmd` 10 Ngày bị lỗi ở Ngày 6 (lặp lại `day_plan` D1–D5) hoặc crash do rò rỉ/hết id**: Quang (M2) & Minh (M4) phải test kỹ chuyển tiếp Ngày 5 → Ngày 6 và chạy đủ 10 Ngày không lỗi (`days_completed: 10`, `crashes: 0`) trước **2:45**.
3. **Quên công bố GitHub Release `v1.0.0` hoặc quên đính kèm file đóng gói / thiếu `docs/members/<handle>.md`**: Chốt mọi commit trước **2:55** để An (M6) tạo tag `phase-4`, xuất Release `v1.0.0` trên GitHub và kiểm tra lại đường link trước **3:00**.
