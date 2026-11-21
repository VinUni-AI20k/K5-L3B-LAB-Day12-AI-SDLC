# Dữ liệu Gather chuẩn bị cho Phase 4

- Bổ sung `freshness` ở gốc contract, cùng vị trí và tên khóa với dữ liệu preview Phase 3. Chưa đổi `contract_version`: giao diện hiện chỉ nhận 1.1/1.2, còn runner, scenario và kho chưa tích hợp schema 1.2.
- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out /tmp/gather-contract-check.jsonl`: mã thoát 0.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`: 64 test, 7 thất bại; cùng bảy lỗi đã ghi nhận trước thay đổi (fixture `keo_neo`, `--days`, `pause` và bốn test tích hợp độ tươi Phase 3).
- Dữ liệu mới ở gốc chưa được runner đưa vào `tuning.freshness` cho Gather; bật logic cá thể cần Integrator hoàn tất scenario, kho và runner cùng Quán.
