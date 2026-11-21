# Ma trận truy vết Phase 4 (TICKET-04 · Phát hành v1.0.0 · Test Contract v1.3)

- **QA:** `hungdt31` · **Commit được kiểm:** `75698f3` (nhánh `feat/p4-qa-soak-verification`) · Python 3.14.4 / Linux.
- Ticket không đánh số AC, nên QA đặt mã `AC-P4-xx` theo thứ tự mục trong TICKET-04 và DoD.
- **Phải chạy lại bảng này trên commit gắn tag `phase-4`** trước 3:00, rồi sửa cột Kết quả nếu khác.

| AC | Yêu cầu (TICKET-04) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | `contract_version: "1.3"`; khai `bench_cmd` và `soak_cmd` ở gốc `game.contract.json` | Đọc contract; `python3 tools/check_team.py` | [game.contract.json](../../game.contract.json), [check_team.log](../proof/phase-4/check_team.log) | **Một phần**: có `1.3` và `soak_cmd`; **chưa có `bench_cmd`** |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh lõi có render 1280×720 (làm nóng 3 s, đo 30 s), xuất `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` | Chạy lệnh; tính lại `avg_fps = frames / measured_s`; báo cáo các mốc 60 / 30 FPS và load ≤ 10 s | `docs/proof/phase-4/bench.json` (chưa có) | **Chưa đạt**: chưa có lệnh. Xem "Rủi ro" |
| AC-P4-03 | `soak_cmd --seed 7 --days 10 --out soak.json`: có `days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s`; đạt khi `days_completed = days` và `crashes = 0`; tất định ở các trường gameplay | Chạy 2 lần, so mọi trường trừ `duration_s`; `tests/test_soak_p4.py` | [soak.json](../proof/phase-4/soak.json), [soak-run2.json](../proof/phase-4/soak-run2.json), [soak.log](../proof/phase-4/soak.log) | **Đạt**: 10/10 Ngày, 0 crash, ~8.5 s, hai lần giống nhau |
| AC-P4-04 | Mỗi Ngày đi qua gather → quan → shop; kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt | `tools/qa_soak_trace.py 7 10`; `test_soak_p4::test_day6_reuses_d1_plan` (đỏ `KeyError: 6` trước bản sửa `day.py`) | [soak-trace.log](../proof/phase-4/soak-trace.log) | **Đạt**: `day_plan` 10/10 khớp D((n−1) mod 5 + 1); id `I1..I113` không trùng; nâng cấp giữ xuyên Ngày; `earned` tăng đều 203 → 3110 |
| AC-P4-05 | Gameplay, tuning, kho và JSONL giữ như v1.2 | Chạy lại inputs P3 trên `75698f3`, `cmp` với bằng chứng P3 | [regression-smoke.log](../proof/phase-4/regression-smoke.log) | **Đạt**: integration gather/kho/quan và day5 giống **từng byte** P3 |
| AC-P4-06 | Regression P1–P3 còn hiệu lực đạt | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`; `tools/qa_check_day.py` | [unittest.log](../proof/phase-4/unittest.log), regression-smoke.log | **Đạt**: 89/89 (86 của P1–P3 + 3 test soak); 5 Ngày kho bàn giao đúng, không có đơn ngoài kế hoạch |
| AC-P4-07 | Ba cảnh báo có chữ hoặc biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) và chế độ tương phản cao; chơi thử cả ba ở chế độ đó | Chơi thủ công, chụp ảnh | `docs/proof/phase-4/hud-*.png` (chưa có) | **Chưa kiểm**: chờ lát UI |
| AC-P4-08 | Từ clone sạch, chạy được bản có giao diện theo `README.md` trong ≤ 3 lệnh (macOS/Linux); README ghi môi trường, điều khiển, lệnh test, headless, benchmark | Clone sạch rồi chạy test, soak, `chonoi.live --mode day` (kiểm `GET /` 200 và `/state`) | [clean-clone.log](../proof/phase-4/clean-clone.log) | **Một phần**: các lệnh chạy được, không cần cài thêm gói (3 lệnh: `git clone`, `cd`, `python3 -m chonoi.live --mode day`); **README chưa cập nhật** phần lệnh, điều khiển, benchmark |
| AC-P4-09 | GitHub Release v1.0.0 có bản đóng gói chạy được, release notes; `CHANGELOG.md` theo phase; rà `CREDITS.md`, `LICENSE` | Xem Release, CHANGELOG, CREDITS, LICENSE | [CHANGELOG.md](../../CHANGELOG.md) | **Một phần**: CHANGELOG đã có phase-1..3 và bổ sung phase-4 (QA); **chưa có Release, `LICENSE`** |
| AC-P4-10 | Tag `phase-4` và Release v1.0.0 cùng trỏ một commit trên `main`, trước 3:00 | `git ls-remote --tags origin` | | **Chưa**. Ghi chú: `phase-3` vẫn trỏ `39be0e1` (đỏ 20/78); bản xanh là `a7a8ccd` |
| AC-P4-11 | Cập nhật `docs/clarify.md`, `docs/ai-usage-log.md`; retro rà hành động P2; `docs/members/<handle>.md` đủ người | Đọc file | [clarify.md](../clarify.md), [ai-usage-log.md](../ai-usage-log.md), [members/](../members/) | **Một phần**: QA đã cập nhật phần của mình; retro P4 và phản tư của người khác do từng người viết |
| AC-P4-12 | Mở rộng (nhóm 6 người ≥ 2 mục: leaderboard, phụ đề SFX, …) có test và bằng chứng | | | **Chưa làm** |

## Rủi ro / việc chưa làm (cần chốt người nhận trước 3:00)

- **`bench_cmd` chưa có (AC-P4-02).** Cảnh render nằm trong trình duyệt (`chonoi/web/index.html`, canvas + `requestAnimationFrame`).
  - QA đã thử điều khiển Firefox headless để đo, nhưng máy QA dùng Firefox bản snap: không dùng được profile trong `/tmp` và không dừng được tiến trình. Vì vậy QA không tự làm bench.
  - Đề xuất cho lát UI: thêm chế độ `?bench=1` trong `index.html`. Chế độ này ghi thời gian từng khung hình (sau 3 s làm nóng, đo 30 s) rồi `POST /bench`. `chonoi/bench.py` khởi `LiveServer` (gather, seed 42, Út Sen đứng ở bến), mở trình duyệt 1280×720, nhận kết quả và tính 5 trường.
  - Thay vào đó có thể dùng bộ vẽ Python riêng, nhưng khi ấy số đo **không phản ánh giao diện thật**. Nếu chọn cách này phải ghi rõ trong release notes.
- **AC-P4-07:** chưa có chế độ tương phản cao trong UI.
- **AC-P4-08, 09:** README, `LICENSE`, Release v1.0.0 thuộc vai Đóng gói / Release.
- Tag `phase-3` trỏ commit đỏ; nên gắn lại vào `a7a8ccd`.
