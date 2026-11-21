# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Khánh (qockhah253) | Claude Sonnet 5.5 (Claude desktop, chạy cả ở workspace đám mây lẫn máy cá nhân) | Đọc PRD-0 mục F trên lab board, viết `chonoi/sim/quan.py` (lát 3+4) và `tests/test_quan.py` | chưa đo | Test đầu tiên sai: AI truyền cả scenario thay vì khối `quan` và tính kiên nhẫn lúc phục vụ lệch 1 tick; sửa sau khi chạy test (47 test xanh). PRD mục F không nằm trong repo nên AI phải đọc từ lab board. Một số chi tiết PRD không nói (id khách mới, giá trị mặc định `base_price`/`tip`) là giả định, đã ghi ở `docs/clarify.md`. |
