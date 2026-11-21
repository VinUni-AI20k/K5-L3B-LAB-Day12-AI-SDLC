# Kế hoạch Phase 1–2 (TV3)

## Phase 1
- Mục tiêu: khách / reserved / spawn / no_dish; proof `docs/proof/phase-1/tv3-customers.md`.

## Phase 2 (đang làm)
- Mục tiêu: 6 món, B2/T2–T4, `day_plan` D1–D5, lọc món theo kế hoạch trong day; quán độc lập đủ menu.
- Việc TV3: `game.contract.json` (menu/quan/day_plan/shop stub) · `chonoi/day_plan.py` · lọc trong `QuanSim._cookable_dishes` · test `tests/test_quan_plan_p2.py` · proof `docs/proof/phase-2/tv3-menu-plan.md`.
- Phụ thuộc: TV4 gắn `--mode day` + gọi `plan_for_day`; TV5 đọc day_plan trên HUD.
- Rủi ro: đổi số bàn làm test “bàn bận” phải chiếm cả 4 bàn; đụng contract với TV1/TV2 khi bump `1.1`.
