# Trần Xuân Lộc — phản tư cá nhân (≤ 200 từ)

- **Mã số sinh viên** `2A202603951`
- **Tài khoản GitHub** `Kaylez-TXL`

> Bản nháp ghi nhận công việc Phase 1. Phần tự đánh giá và các lượt review sẽ bổ sung sau.

- Tôi đã làm (kèm link commit):
  - Phase 1 · QA lead. Viết 9 test hộp đen cho giao kho, tính tất định, các trường hợp ở tick cuối và cấu trúc sự kiện. [Commit c82ea72](https://github.com/justapea25/K5-L3B-LAB-Day12-AI-SDLC-MATH/commit/c82ea72) · [Bộ test tích hợp](../../tests/test_integration.py) · [Ma trận Phase 1](../verification/phase-1.md) · [Bằng chứng](../proof/phase-1/qa-headless.md)
- Tôi đã review (kèm link):
  - Đối chiếu kết quả chạy trên `origin/main` và hai nhánh luật đang phát triển với PRD-0 mục E–G. [Kết quả đối chiếu](../proof/phase-1/qa-headless.md#kiểm-tra-các-nhánh-đang-phát-triển)
- AI sai ở đâu và tôi phát hiện thế nào:
  - Bản điền đầu dùng handle thay cho họ tên trong `TEAM.md`. Lỗi được phát hiện khi rà lại hồ sơ và đã sửa thành Trần Xuân Lộc.
- Điều tôi học được:
  - Luồng bàn giao kho có thể chạy đúng dù dữ liệu sự kiện còn lệch hợp đồng. Cần kiểm tra cả hai và ghi commit của từng lần chạy vào bằng chứng.
