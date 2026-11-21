# Kiểm tra Gather và benchmark Phase 4

- Sửa `p1_low_fps` theo ticket: nghịch đảo thời gian trung bình của `max(1, ceil(0.01 × frames))` khung chậm nhất. `tests/test_bench_metrics.py` kiểm tra cả trường hợp một và nhiều khung chậm.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`: chạy 64 test; báo 4 failure (một test `--days`, ba failure thuộc cùng test pause). Các test Gather độ tươi và bàn giao kho Phase 3 đạt trên bản hiện tại.
- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out /tmp/chonoi-gather-phase4.jsonl`: thành công.
- `python3 -m chonoi.bench --seed 42 --duration 30 --out /tmp/chonoi-bench-phase4.json`: chưa đo được vì môi trường chạy không tìm thấy Chrome hoặc Chromium. Cần chạy lại với trình duyệt được cài hoặc chỉ định `CHONOI_BROWSER`, trên commit bàn giao, và lưu kết quả thật.
