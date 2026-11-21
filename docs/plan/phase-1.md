# Kế hoạch Phase 1 (PRD-0 · Test Contract v1.0)

- **Mục tiêu:** Hoàn thiện lõi 2 buổi (`gather` và `quan`) chơi được riêng và nối nhau qua file kho (`--inventory-out` → `--inventory`), HUD tối thiểu đọc được và bộ test/bằng chứng trên `main` tại tag `phase-1`.
- **Việc / người / phụ thuộc:**
  - `tranha1764` (`sim/gather` — Lát 1): bơi, oxy, ngạt, chặn biên, giỏ (`feat/gather-oxygen-hold`). Phụ thuộc: contract v1.0.
  - `ngthanhtamtb` (`sim/gather` — Lát 2): hái nút, bắt cá, cập bến, ghi file kho nguyên tử (`feat/gather-slice-2`). Phụ thuộc: schema kho `docs/contracts/`.
  - `danhhieu204ns` (`sim/quan` — Lát 3): khách đến theo lịch, giữ chỗ nguyên liệu, kiên nhẫn, `no_dish`, `customer_left` (`hieumd`). Phụ thuộc: `inventory.sample.json`.
  - `ngominhcuong` (`sim/quan` — Lát 4): bếp, bưng, phục vụ, tiền, boa, uy tín, hết ca `quan_end` (`feat/quan-cook-serve`). Phụ thuộc: `inventory.sample.json` và gộp với Lát 3.
  - `nguyenquangtiep` (`client/ui`): HUD buổi sáng/tối và luồng `--continue-quan` trên giao diện web (`ui/cho-noi-hud`). Phụ thuộc: snapshot từ `gather`/`quan`.
  - `hungdt31` (`qa`): test đơn vị, smoke 2 tiến trình, `docs/verification/phase-1.md` và `docs/proof/phase-1/` (`feat/qa-v1`). Phụ thuộc: merge đủ 4 lát trên `main`.
- **Rủi ro:**
  - Lát 3 & Lát 4 sửa chung `chonoi/sim/quan.py` → cần rebase/merge sớm và giữ ranh giới hàm rõ ràng.
  - Khác biệt `python` vs `python3` trên Windows khi chạy subprocess smoke test → xác nhận thêm qua CI `ubuntu-latest`.
