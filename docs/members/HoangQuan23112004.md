# HoangQuan23112004 — phản tư cá nhân

- **Tôi đã làm:**
  - P1 (`b580cbf`): lát 4 `chonoi/sim/quan.py` (bếp, bưng, phục vụ, boa, tiền, uy tín, đóng ca) + 10 test `tests/test_quan_lat4.py`.
  - P2 (`f9a37c1`, PR #5): kiểm `menu_filter` theo kế hoạch Ngày + 7 test `tests/test_p2_quan_shop.py` (2 bếp/4 bàn/6 món, `ShopSim`).
  - P3 (`5abdad0`, PR #9): mở rộng Cháy món (`burn`) trong `quan.py`, chuyển test sang v1.2, thêm 5 test `tests/test_p3_quan_fresh_burn.py`.
  - P4: bật `burn` (`burn_s: 20`) + test hộp đen; đóng gói (`README.md`, `CREDITS.md`, `LICENSE`, `tools/package_release.py`).
- **Phối hợp / hỗ trợ:** đối chiếu hợp đồng lát 3 ↔ 4 và rà `quan.py` khi tích hợp cùng `22520160` và `NgChiVinh`.
- **AI sai & cách phát hiện:** P1 tạo 2 fixture sai PRD mục D (phát hiện khi ghép `scenario.py` lát 3); P2 viết trùng `ShopSim` do nhánh local cũ chậm hơn `main` → reset theo `origin/main` và chạy full test.
- **Bài học:** luôn `git pull` trước khi code nhánh riêng, kiểm ca biên theo PRD và chạy cả bộ test trước khi mở PR.
