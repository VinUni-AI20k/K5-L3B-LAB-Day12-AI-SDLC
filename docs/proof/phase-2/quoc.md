# Phase 2 — phần khách của Quoosc

Trạng thái: triển khai phần độc lập, chưa nghiệm thu Phase 2. `QuanSim` nhận `menu_filter` tùy chọn qua constructor theo `docs/plan/phan-chia-cong-viec.md`; khi có, chỉ chọn món trong filter và đủ nguyên liệu. `None` giữ menu đầy đủ, filter rỗng không sinh khách; món không có trong menu bị từ chối. Giá trị số của kế hoạch chưa được diễn giải thành hạn mức.

`python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof`: 90 tests, exit 0, 9/9 bước, headless gather/quán tất định; Python 3.11 trên Windows với shim `python3` tạm. `tests/test_p2_quoc.py` dùng tuning sao chép: hai bếp, bốn bàn, lịch 120 + 900k; xác nhận năm lượt khách, tái sử dụng bàn sau khi hết kiên nhẫn, lọc món, kế hoạch rỗng và món sai. Đây là kiểm thử giả lập, không chứng minh dữ liệu chính thức v1.1. Test giao diện `menu_filter` trước sửa thất bại do constructor thiếu tham số, sau sửa đạt.

Chưa có `DaySim` gọi constructor với kế hoạch; chưa có contract v1.1 với bốn bàn, hai bếp và sáu món. Cần PO/integrator xác nhận schema, ý nghĩa số lượng món, thời điểm tạo kế hoạch, và giao diện truyền trước khi tích hợp. Không sửa contract khóa. Phase 1 vẫn có D-01..D-09 chưa chốt và Q4-F1 trong `../phase-1/q3/q4-review.md`.

Review: khách `waiting` thiếu `reserved` được coi là đã có món nếu `hand` trùng mã món; với nhiều khách cùng món, không có ID liên kết món trên tay và khách. Quy tắc này có thể làm nhiều khách mất reservation. Cần thiết kế cùng Q4, chưa coi là nghiệm thu. Proof Phase 1 trước merge là kết quả lịch sử; regression 90 test ở trên là kết quả mới.
