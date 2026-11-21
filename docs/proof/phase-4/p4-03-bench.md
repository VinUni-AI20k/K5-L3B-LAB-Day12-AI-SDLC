# P4-03 · Benchmark cảnh lặn (AC-P4-02)

Chạy từ gốc repo trên Windows 11 x64, Python 3.12.10, contract v1.2 tại `330b884`. Lệnh đề xuất cho `bench_cmd` của P4-02 là `python3 -m chonoi.bench`, mặc định ghi `bench.json` ở thư mục hiện tại.

```bash
python3 -m chonoi.bench --out docs/proof/phase-4/bench.json
```

| Chỉ số | Kết quả |
|---|---:|
| FPS trung bình | 522,28 |
| FPS của 1% khung chậm nhất | 172,80 |
| Số khung đã vẽ | 5.224 |
| Thời lượng đo | 10,002 s |
| Từ đọc contract đến khung đầu tiên | 18,47 ms |

Số liệu gốc nằm trong [bench.json](bench.json). Bộ vẽ phần mềm tô bộ đệm RGB 1280×720 mỗi khung, vẽ bến, nút hái, đàn cá, Cá Sấu và nhân vật theo snapshot. Lệnh dùng seed 1, chuẩn bị trước một lượt bơi theo kịch bản rồi lặp lại các snapshot để đo. FPS ở đây chỉ phản ánh việc vẽ trong bộ nhớ. `load_ms` đo từ lúc đọc contract đến khi vẽ xong khung đầu tiên. `p1_low_fps` là nghịch đảo của thời gian trung bình của 1% khung chậm nhất, làm tròn số khung lên.

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` đạt 355/355. Ba ca benchmark kiểm nhân vật thay đổi vị trí trên bộ đệm, năm trường JSON và cách từ chối thời lượng không hợp lệ.
- Smoke Phase 1 đạt 27/27, Phase 2 đạt 15/15 và Phase 3 đạt 13/13. Kiểm tất định và kiểm hard-code đều đạt.
