# Kiểm chứng P3-03, AC-P3-02

Chạy trên Windows với Python 3.12. Giỏ cá thể bật khi dựng `GatherSim` với contract v1.2. Mục P3-08 sẽ nối phiên bản từ CLI và bật manifest sau khi hai pha dùng cùng schema.

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` — **294/294 đạt**. Sáu ca mới trong `tests/test_p3_gather.py` kiểm qua ngưỡng ươn, giữ ô giỏ, ID không tái cấp, hái ở tick cuối, mất đồ LIFO và kho rỗng khi ngất. Các ca v1.1 tiếp tục kiểm schema đếm.
- `python3 tools/check_determinism.py` — JSONL giống từng byte qua hai lần chạy của `gather`, `quan`, `day`, seed 1. Lệnh chạy manifest hiện tại (v1.1); ca v1.2 nằm trong bộ unit test.
- `python3 tools/check_no_hardcode.py` — đạt.

Độ tươi giảm bằng số nguyên qua `Freshness`. Mảng snapshot, kho bàn giao và đồ mất xuất điểm tươi. Các sự kiện ươn cùng tick theo ID, còn giỏ giữ thứ tự nhặt. Giả định về thứ tự hao và payload `spoiled` ghi trong `docs/clarify.md`.
