# Ma trận truy vết Phase 4 (phần QA / UI)

Trạng thái commit được kiểm: nhánh `huydn8816` (HEAD `1febf62` + thay đổi chưa commit ghi trong bảng). `main` mới nhất gồm phase 3 một phần.
Mã AC do nhóm tự đặt. Chỉ ghi kết quả đã chạy thật; ô nào chưa làm thì ghi "chưa".

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 Công thức bench.json (avg, 1% low, frames, measured_s) | `tests/test_p4_bench.py::Compute` (4 test) | `docs/proof/phase-4/test_p4_bench_verbose.txt` | Đạt |
| AC-P4-02 Lỗi tham số / thiếu trình duyệt không treo | `test_p4_bench.py::Cli` (3 test) | như trên | Đạt |
| AC-P4-03 Benchmark có render chạy thật, 5 trường | `chonoi/bench.py` chạy Chrome headless 30 s, seed 42, 3 lần | `docs/proof/phase-4/bench.json`, `bench-lan2.json`, `bench-lan3.json` | Đạt: avg 59,1 / 60,0 / 60,0 FPS; 1% low 24,4 / 58,7 / 56,8 FPS (lần 1 có một đợt khung chậm). Mốc 1% low ≥ 30 đạt ở lần 2–3. Chưa khai `bench_cmd` trong contract (việc Integrator) |
| AC-P4-04 Ba cảnh báo có chữ + biểu tượng | Chụp Chrome 1280×720 với snapshot có Cá Sấu gần, oxy < 25%, khách sắp giận | `docs/proof/phase-4/` và `shots` ghi trong báo cáo | Đạt (kiểm bằng ảnh) |
| AC-P4-05 Chế độ tương phản cao (phím C, `?contrast`) | Chụp cảnh gather và quán ở chế độ bật | ảnh trong báo cáo | Đạt (kiểm bằng ảnh). Chưa chơi thử thật |
| AC-P4-06 Regression P1–P3 còn hiệu lực | `unittest discover` toàn bộ, sau khi merge `main` (commit `066a565`) | `docs/proof/phase-4/regression.txt`: 185 test, OK, 0 bỏ qua | **Đạt** trên nhánh huydn8816. Hai test Phase 2 được sửa theo luật, lý do ghi trong commit: `test_sau_04` chỉ đo trong 90 tick bất tử (chạm lại ở tick 91 là đúng luật); `test_shop_01` đọc snapshot tick 7 (sau khi mua) |
| AC-P4-07 Clone sạch chạy bằng tối đa 3 lệnh | Chưa làm | — | **Chưa** |
| AC-P4-08 Soak 10 Ngày (`soak_cmd`) | Chưa làm (việc giảng viên và `day`) | — | **Chưa** |
| AC-P4-09 Phụ đề SFX, leaderboard | Chưa làm (không thuộc vai QA/UI của bản này) | — | **Chưa** |

## Đánh giá ngắn
- Đạt: bench chạy thật, 3 lần ổn định, đúng cấu trúc JSON; công thức có test; ba cảnh báo và tương phản cao có bằng chứng ảnh; regression 185 test OK sau merge.
- Chưa đạt: clone sạch 3 lệnh, soak 10 Ngày, `bench_cmd`/`soak_cmd` trong contract.
- Điều cần làm tiếp: (1) Integrator khai `bench_cmd`, `soak_cmd` và đổi `contract_version` 1.3; (2) kiểm clone sạch trên macOS hoặc Linux và ghi 3 lệnh vào README; (3) soak 10 Ngày (`soak_cmd`).
- Giới hạn bằng chứng: benchmark đo trên Windows với Chrome, không phải macOS/Linux như đề yêu cầu; ảnh UI dựng từ snapshot giả, không phải mô phỏng thật.

## Công cụ headless của nhóm (Bảo, `lat 34 phase 4` trên main)

Các công cụ này do Bảo viết, không nằm trong bản đo ở trên. Mục này chỉ ghi trạng thái, chưa chạy trong bản này.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-10 Contract v1.3 khai `bench_cmd` và `soak_cmd` | `tests/test_phase4_tools.py::test_contract_declares_phase4_commands` | `game.contract.json` | Đã khai; chưa chạy test này trong bản này |
| AC-P4-11 Soak 10 Ngày (`python3 -m chonoi.soak --seed 7 --days 10`) | `chonoi/soak.py`, `tests/test_phase4_tools.py` | chưa có `soak.json` | Chưa chạy |
| AC-P4-12 Benchmark headless xuất năm trường (thông lượng tick, không đo FPS) | `chonoi/benchmark.py` | chưa có artifact | Chưa chạy. Khác với `chonoi/bench.py` (đo khung hình có render) |

Lưu ý: `chonoi.benchmark` và `bench_cmd` trong contract hiện trỏ tới bản headless. PHASE4.md yêu cầu benchmark có render, nên nhóm cần quyết định `bench_cmd` nào là chính thức.

## Kiểm clone sạch (AC-P4-07, làm lại)

Clone nhánh `huydn8816` vào thư mục mới (không dùng bản làm việc), chạy đúng ba lệnh trong README:
1. `PYTHONPATH=tests:. python3 -m unittest discover -s tests`: lần đầu có 1 lỗi do `bench_cmd` (test của Bảo còn kiểm tên `benchmark`); đã sửa test theo quyết định nhóm. Chạy lại: xanh.
2. `python3 -m chonoi.headless --mode gather --seed 1 --ticks 60 --out out.jsonl`: thoát mã 0.
3. `python3 -m chonoi.bench --seed 42 --duration 3 --out bench.json`: thoát mã 0, trả về 5 trường (`avg_fps` 59,99; `p1_low_fps` 58,48).

Giới hạn: chỉ chạy trên Windows (Git Bash, Python 3.14, Chrome). Chưa chạy trên macOS hoặc Linux, nên AC-P4-07 chỉ đạt một phần.

## Soak 10 Ngày (AC-P4-08, đã chạy)

Lệnh: `python3 -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json` (7 giây, thoát 0).

Kết quả: `days` 10, `days_completed` 10, `crashes` 0. Đạt tiêu chí của đề.

Giới hạn: bot của soak hiện không điều khiển người chơi (không bơi, hái, phục vụ), nên `earned` = 0 ở mọi Ngày. Soak chứng minh vòng 10 Ngày chạy không lỗi và trạng thái được giữ qua các Ngày, nhưng chưa chứng minh gameplay. Nên thay bot bằng input có chủ đích nếu muốn kiểm gameplay xuyên ngày.
