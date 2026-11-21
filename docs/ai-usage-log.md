# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | D | Claude Code / Claude Haiku 5.5 | Lát 4 trong `chonoi/sim/quan.py`: bếp (cook_started, dish_ready, dish_picked), phục vụ và boa (served), trả tiền (paid, closing), `_drop_order`; viết `tests/test_lat4_quan.py` (13 test) và `tests/test_lat4_headless.py` (5 test) |  | Bản đầu ghi sai kỳ vọng tiền khi phục vụ lúc hết ca (ghi 40, đúng là 48 = 40 + boa 8), sửa sau khi test đỏ. Fixture test ban đầu giữ chỗ vượt kho, khung mới của C chặn lỗi này, sửa fixture chứ không sửa luật. Phải viết lại hàm khi khung của C đổi tên `_settle_eaten` thành `_pay_customers`. |
