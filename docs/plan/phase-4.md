# Kế hoạch Phase 4 — TICKET-04 Phát hành v1.0.0 (hạn tag `phase-4` + Release v1.0.0 lúc 3:00)

Đề: [`docs/prd/phase-4.md`](../prd/phase-4.md). Làm trên nhánh ngắn của mình → PR vào `main` (Integrator chạy cả bộ test
trước khi merge — hành động retro P2). Gameplay, tuning, kho, JSONL **giữ nguyên v1.2**.

## Việc / người / phụ thuộc

| # | Việc | Người | File chính | AC |
|---|---|---|---|---|
| 1 | Contract v1.3 (`contract_version`, `bench_cmd`, `soak_cmd` ở gốc); **bench có render** `--seed 42 --duration 30 --out bench.json` (cảnh lặn lõi, Út Sen đứng ở bến, 1280×720, làm nóng 3 s, 5 trường JSON); release notes, CHANGELOG Phase 4, tag `phase-4` + GitHub Release v1.0.0 | NgChiVinh (Release/Integrator) | `game.contract.json`, `chonoi/contract.py`, `chonoi/bench.py`, `CHANGELOG.md` | AC-P4-01, 02, 08 |
| 2 | **Soak** `--seed 7 --days 10 --out soak.json`: 10 Ngày một tiến trình, kế hoạch D1–D5 lặp ở Ngày 6–10, bot/input tất định, `days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s` | TrungHieuPh | `chonoi/soak.py`, `chonoi/day.py` (lặp kế hoạch khi > 5 Ngày) | AC-P4-03 |
| 3 | **Cảnh báo dễ nhận biết**: thủy quái gần, oxy sắp hết, khách sắp giận — chữ/biểu tượng; **chế độ tương phản cao** (phím bật/tắt); chơi thử cả 3 cảnh báo ở chế độ đó; điều phối **retro cuối** | truclamld (UI + Scrum) | `chonoi/web/index.html`, `tools/hud_check.py`, `docs/retro.md` | AC-P4-04 |
| 4 | **Đóng gói**: thử clone sạch ≤ 3 lệnh (macOS/Linux), README ghi yêu cầu môi trường, điều khiển, test, headless, bench, soak; tạo gói chạy được cho Release; rà `CREDITS.md`, `LICENSE`. **Mở rộng 1: Cháy món** — bật `burn` trong `extensions` + `burn_s: 20`, test và bằng chứng | HoangQuan23112004 | `README.md`, `CREDITS.md`, `LICENSE`, `game.contract.json` (burn), `chonoi/sim/quan.py` | AC-P4-05, 06 |
| 5 | **Mở rộng 2: Bảng xếp hạng** — `extensions: leaderboard`, top 10 bền vững, headless `day` nhận cặp `--leaderboard --player-name` (thiếu cờ / sai mode → mã 2), `run_cmd --export-leaderboard`, test với store riêng | 22520160 | `chonoi/leaderboard.py`, `chonoi/headless.py`, `chonoi/live.py` | AC-P4-07 |
| 6 | **Bench/QA**: chạy bench + soak + regression P1–P3 + smoke trên commit bàn giao, lưu `docs/proof/phase-4/`, ma trận `docs/verification/phase-4.md` | khoa-asta | `docs/proof/phase-4/`, `docs/verification/phase-4.md` | tất cả |
| 7 | **Mỗi người**: `docs/members/<handle>.md` (≤ 200 từ: phần mình làm kèm commit, đã giúp ai, AI sai ở đâu, bài học) + 1 dòng `docs/ai-usage-log.md` Phase 4 | cả nhóm | `docs/members/`, `docs/ai-usage-log.md` | AC-P4-09 |

## Mốc
- Phút 0–15: #1–#6 song song. Contract v1.3 (#1) lên `main` sớm nhất để #2, #4, #5 khai lệnh/extensions đúng chỗ.
- Phút 15–25: retro + phản tư cá nhân; phút 20 standup, người xong hỗ trợ lát trễ.
- Phút 25–30: Integrator chạy bằng chứng trên đúng commit bàn giao → tag `phase-4` + Release v1.0.0 cùng commit.

## Rủi ro
- Bench "có render": client vẽ trên trình duyệt; bench Python phải tự render khung 1280×720 của cảnh lặn — ghi rõ cách đo và giới hạn trong release notes.
- Bật `burn` đổi luật quán so với lõi → kiểm regression P1–P3; nếu lệch lõi thì chỉ bật khi khai trong `extensions` (headless lõi giữ `burn_s: null`).
- Hết giờ: tag + Release đúng 3:00 với phần đã xong, ghi trung thực phần chưa làm.
