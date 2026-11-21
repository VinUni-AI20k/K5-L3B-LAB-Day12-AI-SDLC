# Gather Phase 3 — kiểm tra độc lập

`PYTHONPATH=tests:. python3 -m unittest tests.test_gather_freshness -v`: 3 test đạt. Các ca kiểm tra ngưỡng 30, ID mới sau fixture, hàng mới chưa hao cùng bước và rơi giỏ LIFO khi ngất.

`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`: 57 test, 3 thất bại. Các lỗi hiện tại: scenario Phase 2 từ chối `keo_neo` trong giỏ; CLI chưa nhận `--days`; input chưa nhận `pause`.

Tích hợp còn chờ: cung cấp `tuning.freshness`, xác thực fixture cá thể, sửa bộ ghi/đọc kho và runner để nhận mảng cá thể, và chia sẻ IdAllocator xuyên ngày. Các thành phần chung hiện vẫn dùng schema đếm; chưa thể kiểm tra giao tiếp qua headless v1.2.
