# Gather Phase 2 — kiểm chứng

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`: 48 test đạt.
- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out /tmp/gather-phase2.jsonl`: chạy thành công.
- `tests/test_gather_phase2.py` kiểm tra phản xạ cá, sinh cá đúng tick, fixture cá đứng yên và va chạm cá sấu với rơi giỏ LIFO.
- Test snapshot Phase 1 được cập nhật từ 6 đàn cố định sang số đàn khởi tạo trong contract vì Phase 2 yêu cầu 8 đàn.
- Cấu hình Gather đã mở rộng; phiên bản contract tổng thể vẫn là 1.0 vì Quán, mode day và các phần Phase 2 khác chưa tích hợp. Giao diện hiện chưa vẽ cá sấu.

Các dòng trên ghi kết quả nhánh Gather khi triển khai. Trên `main` tại `881c4c4`, manifest là v1.1. Cá phản xạ, sinh theo lịch, fixture tắt ngẫu nhiên và ca Cá Sấu làm ngất đều đạt. Ca va chạm có `keo_neo` trong giỏ bị chặn bởi validator còn dùng bộ mã Phase 1. [Kết quả trên main](integration.md#các-ca-chưa-đạt)
