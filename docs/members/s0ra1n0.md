# s0ra1n0 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):** lát 1 của gather (oxy, ngạt, Máu, ngất) trên nhánh `feat/lat-1`.
  - [`03f8514`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/03f8514): `_update_oxygen`, 13 test hộp đen, bằng chứng `docs/proof/phase-1/lat1.md`.
  - [`9cfd7b0`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/9cfd7b0): chép PRD-0 vào `docs/prd/phase-1.md` cho cả nhóm và agent đọc.
- **Tôi đã review (kèm link):** … *(điền link PR lát 2 khi đọc xong)*
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Công cụ tóm tắt báo lab board "không có yêu cầu Phase 1". Tôi mở trang trong trình duyệt thì thấy có đủ nội dung.
  - AI tự điền hai đoạn bị cắt trên board. Tôi giữ lại nhưng yêu cầu đánh dấu "suy ra" trong file.
  - Test lát 1 xanh ngay lần đầu. Tôi đối chiếu thêm bằng một lần chạy headless thật và tính tay mốc tick.
- **Điều tôi học được:** đọc kỹ thứ tự xử lý từng bước trong PRD trước khi code. Một lệch nhỏ như "đếm ngạt cả bước vừa chạm 0" làm sai tick của sự kiện. Viết test hộp đen theo đúng câu chữ PRD giúp bắt chỗ này.
