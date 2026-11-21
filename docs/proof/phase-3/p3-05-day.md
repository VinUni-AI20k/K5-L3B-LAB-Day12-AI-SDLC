# Kiểm chứng P3-05, AC-P3-04

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -q` — **296/296 đạt**. Hai ca mới kiểm giao cùng tick, giữ ID và độ tươi, Shop không hao kho và ID mới không lặp ngày trước.
- `python3 tools/check_determinism.py` và `python3 tools/check_no_hardcode.py` — đạt trên manifest v1.1 hiện tại.

Test v1.2 dựng `DaySim(..., contract_version="1.2")` với `GatherSim` và `ShopSim` thật, dùng fixture thay đầu nhận Quán. Khi gather kết thúc, `day` gửi mảng `inventory` với điểm tươi và `contract_version="1.2"` cho `QuanSim`. Quán trả mảng cá thể qua `snapshot()["stock"]` để Shop giữ nguyên. Quán chịu trách nhiệm kiểm giữ chỗ theo ID trên kho được giao.

Chạy đầu cuối v1.2 cần P3-04 triển khai giao diện Quán và P3-08 truyền phiên bản từ dòng lệnh. Smoke v1.1 tiếp tục dùng kho đếm. Nhánh P3-05 dựa trên P3-03, chỉ có một commit của P3-05 sau commit giỏ cá thể.
