# qockhah253 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - feat(quan): khách, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, tiền (lát 3+4) — `chonoi/sim/quan.py` (PR #3)
  - test(quan): unit test luật quán — `tests/test_quan.py` (PR #3)
  - docs: clarify.md (câu hỏi PO + giả định khi Anh Năm báo not_granted) — PR #5, PR #10
- Tôi đã review (kèm link):
  - PR #8 (Khuê, validate scenario quán): merge thử với main, chạy 88 test đều pass, rồi approve
- AI sai ở đâu và tôi phát hiện thế nào:
  - Test AI viết lúc đầu truyền sai dạng scenario (bọc thêm khóa "quan") và tính sai kiên nhẫn lúc phục vụ lệch 1 tick. Tôi phát hiện khi chạy test thấy fail, rồi đối chiếu lại với luật trong PRD để sửa đúng chỗ.
- Điều tôi học được:
  - Phải tự chạy test và đối chiếu với tài liệu luật, không tin kết quả AI viết ra ngay.
  - Làm việc nhóm cần nhánh riêng + PR + review; lỗi môi trường (Anh Năm not_granted) thì ghi lại và đặt giả định rõ ràng thay vì chặn việc.