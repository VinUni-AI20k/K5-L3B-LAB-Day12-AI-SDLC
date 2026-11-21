# Kế hoạch Phase 1 (≤ 1 trang)

- Mục tiêu: Bàn giao hai ca chơi được (gather + quan), HUD đọc được, smoke hai tiến trình theo Test Contract v1.0. TV3 xong lịch khách / reserved / kiên nhẫn / no_dish trước khi ghép TV4.

- Việc / người / phụ thuộc:
  - TV1 · sinh tồn gather — độc lập; ghép TV2 vào `GatherSim.step`
  - TV2 · hái / bắt / kho — độc lập bằng fixture; xuất kho thật trước phút 25
  - **TV3 · khách + reserved** — dùng kho mẫu; API cho TV4 (`available_stock`, `release_and_cleanup`, spawn/patience); test `tests/test_quan_customers.py`; proof `docs/proof/phase-1/tv3-customers.md`
  - TV4 · bếp / tiền — phụ thuộc helper TV3; sở hữu interact trong `QuanSim.step` (gọi interact trước patience leave)
  - TV5 · HUD / QA / tag — đọc snapshot; smoke mục G

- Rủi ro: đụng `quan.py` step với TV4 → chốt thứ tự mục F sớm; spawn dùng `phase_tick` sau tăng; RNG món chỉ qua `Streams.get("dish_pick")`.
