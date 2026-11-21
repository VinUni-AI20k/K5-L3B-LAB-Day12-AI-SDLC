# Ma trận truy vết Phase 4

Phạm vi lát 3–4 trong lần làm này: công cụ benchmark và soak. Bảng ghi trung thực trạng thái trong môi trường hiện tại; không thay cho kết quả chạy trên commit bàn giao.

| AC | Nội dung | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | Contract v1.3 khai bench_cmd và soak_cmd; benchmark xuất đúng năm trường | tests/test_phase4_tools.py::test_contract_declares_phase4_commands, test_benchmark_emits_five_required_metrics | chonoi/benchmark.py, game.contract.json | Đã triển khai; chưa chạy Python |
| AC-P4-02 | Soak chạy 10 ngày trong một tiến trình, ghi days/days_completed/crashes/results/duration_s | python3 -m chonoi.soak --seed 7 --days 10 --out soak.json | chonoi/soak.py, tests/test_phase4_tools.py | Đã triển khai; chưa chạy Python |
| AC-P4-03 | D1–D5 lặp cho ngày 6–10 | tests/test_phase4_tools.py::test_day_six_to_ten_repeat_five_day_plan | chonoi/sim/day.py | Đã triển khai; chưa chạy Python |
| AC-P4-04 | Chữ/biểu tượng cảnh báo thủy quái, oxy thấp, khách sắp giận; H bật tương phản cao | Chơi thử ba cảnh báo với H bật/tắt | chonoi/web/index.html | Đã triển khai; chưa kiểm bằng trình duyệt |
| AC-P4-05 | Clone sạch, test/headless/benchmark/soak có hướng dẫn | Làm theo README từ môi trường Python mới | README.md, AGENTS.md | Đã cập nhật; chưa thử clone sạch |

## Giới hạn kiểm chứng

- Shell hiện tại không có python, python3 hoặc py; test tự động và artifact bench.json/soak.json chưa được tạo.
- Benchmark hiện đo thông lượng tick của mô phỏng gather, không đo FPS trình duyệt/render. Không dùng kết quả này để kết luận FPS hiển thị.
- Chưa tạo tag/release. Retro nhóm, phản tư từng thành viên, giấy phép và kiểm tra âm thanh/phụ đề vẫn cần nhóm hoàn tất.
