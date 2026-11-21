# Truy vết Phase 4 (TICKET-04, Test Contract v1.3 — Bench render + Soak)

Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → 162 test, OK (151 cũ + 11 mới trong `tests/test_p4_soak.py`).
Chưa commit/tag tại thời điểm ghi — phải chạy lại ở commit gắn tag.

| AC | Nội dung | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 | `contract_version` = "1.3"; khai báo gốc `bench_cmd`, `soak_cmd`; gameplay/tuning/kho/JSONL giữ v1.2 | `game.contract.json`, `chonoi/contract.validate_root`, `test_p4_soak.ContractV13` | Đạt (thiếu khóa ở v1.3 → BadInput; v1.2 không bắt buộc) |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh lõi buổi sáng (gather: độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định, Út Sen đứng yên ở bến), 1280×720, khởi động 3 s rồi đo 30 s | `tools/bench.py`, `client/bench.html`, `client/src/bench.js`, `docs/proof/phase-4/bench.{json,log}` | Đạt (Chrome headless thật, exit 0) |
| AC-P4-03 | Schema bench đúng 5 khóa; avg = frames/measured_s; 1% low = 1/mean(dt) của max(1, ceil(1% frames)) khung chậm nhất | `bench.validate`, `BenchSchemaP4` (stub + artifact thật) | Đạt |
| AC-P4-04 | Không có trình duyệt → mã khác 0, stderr rõ | `test_no_browser_exits_nonzero` (CHONOI_BROWSER sai → mã 2) | Đạt |
| AC-P4-05 | `soak_cmd --seed 7 --days 10`: 10 Ngày gather → quan → shop trong một tiến trình, kế hoạch D1–D5 lặp ở Ngày 6–10, tiền/earned/uy tín/cấp/id xuyên suốt | `tools/soak.py`, `DaySim.plan_for`, `docs/proof/phase-4/soak.{json,log}`, `test_ten_days_pass` | Đạt (days_completed 10/10, crashes 0) |
| AC-P4-06 | Soak tất định theo seed (trừ `duration_s`) | `test_deterministic` (chạy 2 lần so sánh) | Đạt |
| AC-P4-07 | Bot chơi thật (lặn/bắt/hái, cập bến, nấu, bưng, mua nâng cấp, đóng Shop) | `Bot` trong `tools/soak.py`, `test_bot_actually_plays_and_progress_carries` | Đạt một phần — xem ghi chú |

## Số đo bench (máy dev macOS, Chrome headless `--headless=new`, seed 42, 30 s)

| Chỉ số | Đo được | Ngưỡng báo cáo | Kết quả |
|---|---|---|---|
| avg_fps | 60.003 (1801 khung / 30.015 s) | ≥ 60 | Đạt (sát ngưỡng: bị khóa vsync 60 Hz) |
| p1_low_fps | 59.524 | ≥ 30 | Đạt |
| load_ms | 1953 | ≤ 10 000 | Đạt |

Ghi chú trung thực:
- `load_ms` = thời điểm khung đầu cảnh đo (epoch, trong trang) − thời điểm runner khởi chạy Chrome (tham số `t0`), gồm cả khởi động Chrome và hiệu ứng chuyển cảnh. Lần chạy thử 3 s đầu tiên (Chrome lạnh, hồ sơ mới) đo 9909 ms — sát ngưỡng 10 s; lần chính thức 1953 ms. Biến động lớn theo cache đĩa.
- Headless khóa ~60 Hz nên avg_fps không thể vượt 60 nhiều; đây là đo đầu ra rAF, không phải GPU tối đa. Chưa đo trên máy yếu.
- Seed được áp bằng cách thay `Math.random` (mulberry32) trước khi nạp module game; `main.js` không bị sửa (bench.html nạp `src/bench.js` trước `src/main.js`, dùng `?debug` → `window.__chonoi.go("gather")`).

## Kết quả soak (seed 7, 10 Ngày)
earned sau mỗi Shop: 229, 576, 828, 828, 1172, 1409, 1774, 1774, 2107, 2107; uy tín 4.2 → 5; days_completed 10, crashes 0, ~4.8 s.
Ngày 4, 8, 10 bot kiếm 0 (kế hoạch cần cá sâu/ca_keo gần Cá Sấu, bot né quái nên không đủ nguyên liệu) — soak vẫn đạt nhưng bot chưa tối ưu. Bot chỉ mua nâng cấp khi đủ tiền, tối đa một lệnh/tick trong 5 tick đầu Shop.
`--mode day --days` của headless vẫn giới hạn 1..5 (không đổi contract JSONL); soak dùng `Session` trực tiếp.

## Mở rộng (TICKET-04 mục 3) — làm sau Release v1.0.0, chưa có trong tag `phase-4`/`v1.0.0`

Nhóm 3 người nên mở rộng không bắt buộc. Hai mục dưới đây nằm ở các commit **sau** tag; tag và Release không bị gắn lại.
Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → 187 test, OK (170 cũ + 17 mới trong `tests/test_leaderboard_p4.py`).
`pre-push-check`: contract OK, unittest 187 OK, headless gather/quan/day exit 0 (1 Ngày 0.6 s), client JS 31 file OK.

| AC | Nội dung | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-X01 | Headless `day` nhận cặp `--leaderboard <store> --player-name <name>`; ghi **đúng một** mục `{name,score,days_completed,seed}` khi đủ 5 Ngày chuẩn (không scenario, reason `days_complete`); `score` khớp dòng `end` | `RecordP4.test_standard_run_writes_one_entry_matching_end_row`, `test_second_run_appends_exactly_one`, `ext/leaderboard_cli.txt` | Đạt |
| AC-P4-X02 | Không ghi khi lượt không chuẩn: `--days 4`, có `--scenario`, chạm `--ticks` trước khi xong | `RecordP4.test_not_standard_no_entry`, `test_tick_limit_no_entry` | Đạt |
| AC-P4-X03 | Thiếu một cờ hoặc sai mode (`gather`/`quan`) → mã 2, không tạo file đầu ra; store hỏng / tên rỗng / store trùng `--out` → mã 2 | `BadFlagsP4` (4 test), `ext/leaderboard_cli.txt` | Đạt |
| AC-P4-X04 | Top 10, điểm giảm dần, hòa → mục ghi trước đứng trước; mục mới hòa với hạng 10 bị loại | `RankingP4` (3 test) | Đạt |
| AC-P4-X05 | `<run_cmd> --export-leaderboard <out> [--leaderboard <store>]` xuất `{"entries":[…]}`; store chưa có → rỗng; store hỏng → mã 2 | `ExportP4` (4 test), `ext/leaderboard_cli.txt` | Đạt |
| AC-P4-X06 | JSONL không đổi khi có cờ xếp hạng; soak không ghi xếp hạng | `RecordP4.test_jsonl_unchanged_by_flags`, `SoakDoesNotRecordP4` | Đạt |
| AC-P4-X07 | GUI: sau tổng kết 5 Ngày nhập tên → top 10 (localStorage), phím H/U/T không kích hoạt khi đang gõ | `ext/ui_check.mjs` (Chrome headless): `phase` stats→name→board, `typed:"Tester"`, `chonoi.hc` không đổi, không mở điện thoại; ảnh `ext/06-name-entry.png`, `ext/07-leaderboard.png` | Đạt |
| AC-P4-X08 | Phụ đề SFX: phím U bật/tắt và lưu; tự bật khi tắt tiếng; lặp cùng chữ hiện `×n`; tiếng click không có phụ đề | `ui_check.mjs`: `ccStored:"1"`, `linesOn` có `[Cá Sấu cắn] x2` và không có click, `offLines:0`, `mutedLabel:"…Tự bật (tắt tiếng)"` | Đạt |
| AC-P4-X09 | Ba cảnh báo có phụ đề, chơi thử ở chế độ âm thanh tắt / tương phản cao: thủy quái gần (`[Cá Sấu gầm — đang đến gần]`), oxy sắp hết (`[tim đập nhanh — oxy sắp hết]`), khách sắp giận (`[khách T1 càu nhàu — sắp giận]`) | `ui_check.mjs` (`afterOxy`, `quanAngry`), ảnh `ext/02-…`, `ext/03-gather-hc-captions.png`, `ext/04-quan-angry-caption.png` | Đạt một phần — oxy và khách kiểm trong cảnh thật; phụ đề Cá Sấu gần chỉ kiểm qua code (bot không lái tới gần Cá Sấu) |

Ghi chú trung thực:
- `ui_check.mjs` gọi `window.__chonoi` (chỉ có với `?debug`) để nhảy cảnh, đặt oxy/kiên nhẫn của khách cho nhanh tới ngưỡng; không phải người chơi thật đi hết vòng.
  Người phụ trách nên chơi tay một vòng lặn → quán → chợ với âm thanh tắt trước khi gộp.
- Kiểm trên Linux (WSL2), Chrome 1280×720, node 26. Chưa kiểm Safari/Firefox.
