# P4-03 · Benchmark cảnh lặn (AC-P4-02)

Chạy từ gốc repo trên Windows 11 x64, Python 3.12.10, contract v1.2 tại `330b884`. Lệnh đề xuất cho `bench_cmd` của P4-02 là `python3 -m chonoi.bench`; nhận `--seed`, `--duration` (mặc định 30 s), `--warmup` (3 s, không tính vào số đo) và `--out`, đúng dạng lệnh của đề `--seed 42 --duration 30 --out bench.json`.

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
```

| Chỉ số | Kết quả |
|---|---:|
| FPS trung bình | 1.361,42 |
| FPS của 1% khung chậm nhất | 835,98 |
| Số khung đã vẽ | 40.843 |
| Thời lượng đo | 30,000 s (sau 3 s làm nóng) |
| Từ lúc khởi chạy đến khung đầu tiên (`load_ms`) | 135,78 ms |

Số liệu gốc nằm trong [bench.json](bench.json). Bộ vẽ phần mềm tô bộ đệm RGB 1280×720 mỗi khung, vẽ bến, nút hái, đàn cá, Cá Sấu và nhân vật theo snapshot. Lệnh dùng seed 42, chuẩn bị trước một lượt bơi theo kịch bản rồi lặp lại các snapshot để đo. FPS ở đây chỉ phản ánh việc vẽ trong bộ nhớ. `load_ms` đo từ lúc đọc contract đến khi vẽ xong khung đầu tiên. `p1_low_fps` là nghịch đảo của thời gian trung bình của 1% khung chậm nhất, làm tròn số khung lên.

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` đạt 355/355. Ba ca benchmark kiểm nhân vật thay đổi vị trí trên bộ đệm, năm trường JSON và cách từ chối thời lượng không hợp lệ.
- Smoke Phase 1 đạt 27/27, Phase 2 đạt 15/15 và Phase 3 đạt 13/13. Kiểm tất định và kiểm hard-code đều đạt.
- Sửa theo review của D (tích hợp trước khi gộp): thêm `--duration` (`--seconds` vẫn dùng được), làm nóng 3 s, mặc định `--seed 42 --duration 30`, sinh lại `bench.json` bằng đúng lệnh trên (số cũ đo 10 s không làm nóng). Chưa đối chiếu được các thành phần cảnh (độ tươi, Năm Chèo) với Ticket-04: bộ vẽ hiện chưa vẽ độ tươi và Năm Chèo.

## Cập nhật theo Ticket-04 (D đọc đề trên lab board ngày 2026-11-21)
- **Cảnh đo** theo đề: buổi sáng lặn có độ tươi, cá bơi, Cá Sấu và hiệu ứng mặc định; **Út Sen đứng yên ở bến** (không còn bơi). Giỏ có 6 cá thể độ tươi 100 đến 20, HUD vẽ thanh độ tươi (đỏ khi ươn), độ tươi hao theo thời gian; cá và Cá Sấu chuyển động theo sim.
- **Công thức** khớp đề: `p1_low_fps` là nghịch đảo thời gian trung bình của `max(1, ceil(0.01 × frames))` khung chậm nhất; `avg_fps = frames / measured_s`; `frames`, `measured_s` chỉ tính sau làm nóng; `load_ms` tính từ lúc khởi chạy đến khung hình đầu tiên (đầu module, trước các import).
- Mốc báo cáo của đề: avg ≥ 60 FPS, 1% low ≥ 30 FPS, load ≤ 10 s. Số đo trên đạt cả ba (bộ vẽ phần mềm trong bộ nhớ, ghi trung thực: không phải FPS của trình duyệt).
- Chưa rõ "hiệu ứng mặc định" của đề gồm gì; bộ vẽ chỉ tô nền nước gradient, chưa có hiệu ứng riêng.
