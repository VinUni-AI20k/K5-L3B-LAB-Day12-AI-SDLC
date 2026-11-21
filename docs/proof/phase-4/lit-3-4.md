# Bằng chứng lát 3–4 — benchmark và soak

- Contract v1.3 khai bench_cmd = python3 -m chonoi.benchmark và soak_cmd = python3 -m chonoi.soak.
- Benchmark chạy cảnh gather với seed cố định, đo thời gian nạp, throughput theo cửa sổ 250 ms và ghi avg_fps, p1_low_fps, frames, measured_s, load_ms.
- Soak dùng một Session day trong cùng tiến trình, đóng Shop bằng input tất định, giữ trạng thái giữa các ngày và ghi kết quả ở mỗi shop_end.
- Day 6–10 dùng kế hoạch tương ứng D1–D5.
- Test mới: tests/test_phase4_tools.py. Chưa chạy được do môi trường hiện tại không có Python; không có số benchmark/soak giả lập kèm theo.
- Hướng dẫn chạy và các giới hạn được ghi ở docs/verification/phase-4.md.
