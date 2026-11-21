# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Snapshot `day_plan` trong `--mode day` là object của Ngày hiện tại hay mảng cả 5 Ngày? (Phase2.md 4.4 nói "mọi snapshot có day_plan", mục 4.3 dùng mảng cho scenario) | Chưa hỏi Anh Năm. Giả định: UI chấp nhận cả hai dạng (mảng thì chọn theo `day`). Test chỉ kiểm event `day_plan` {dishes, ingredients}, không kiểm dạng trong snapshot | QA tạm, chờ PO |
| 2 | 2026-11-21 | Event `shop_end` reason `time` phát ở tick nào: tick mở Shop + 600 hay +601? ("tự đóng sau 600 tick hoạt động") | Chưa hỏi. Giả định: tick mở Shop + 600 (`test_shop_05`). Lệch 1 tick thì sửa test và ghi lý do trong commit | QA tạm, chờ PO |
| 3 | 2026-11-21 | DayIntro "tự chuyển sau 4 s": đồng hồ giao diện hay mô phỏng có dừng trong 4 s đó? | Chưa hỏi. Giả định: chỉ ở giao diện, mô phỏng vẫn chạy (UI không tác động tick). Nếu cần dừng sim thì phải có lệnh `pause` do UI gửi | UI (huydn8816), chờ PO |
| 4 | 2026-11-21 | Event `day_start`, `day_plan`, `phase_start` ở tick 0 nằm trước hay sau snapshot tick 0 trong JSONL? | Chưa hỏi. Test chỉ kiểm thứ tự tương đối giữa ba event, không kiểm vị trí so với snapshot | QA tạm, chờ PO |
