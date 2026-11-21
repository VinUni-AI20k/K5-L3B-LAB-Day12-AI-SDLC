# TuHoAnh — phản tư cá nhân

- **Tôi đã làm (kèm link commit):**
  - P1-06 (`p1-06-quan-slice3`): khách đến theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, `no_dish`, `customer_left`.
  - P1-07 (`p1-07-quan-slice4`, PR #12, merge `e19d928`): tương tác bếp/bàn, nấu, bưng, phục vụ, tiền/boa, uy tín, `quan_end`.
  - HX-03 (`hx-03-no-hardcode-skill`): tạo tool & skill `check-no-hardcode` quét số hard-code trong `chonoi/sim/`.
- **Tôi đã review (kèm link):**
  - Đọc và đối chiếu bản vá P1-06/P1-08 từ `origin/main` khi resolve conflict ở PR #12; rà kết quả `check_no_hardcode.py` trên `gather.py`.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Lát 3 ban đầu thiếu xử lý một số mặc định scenario và chi tiết đóng ca, phát hiện qua review của nhóm trưởng và test mới trên `main`. Khi merge `origin/main` vào P1-07 xảy ra conflict, mình cho AI đọc cả hai phía và chạy lại đủ 111 unit test + check determinism để xác nhận.
- **Điều tôi học được:**
  - Luôn kéo `main` mới nhất trước khi push, chia nhỏ từng lát việc, và chỉ tin khi có bằng chứng test + check tất định chạy thật.
