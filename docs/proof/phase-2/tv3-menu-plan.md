# TV3 · Phase 2 — Menu, bàn/bếp, day_plan

Chạy:

```bash
PYTHONPATH=tests:. python3 -m unittest tests.test_quan_plan_p2 tests.test_quan_customers -v
```

| Yêu cầu (phan-cong / TICKET-02) | Kết quả |
|---|---|
| `contract_version` 1.1, 6 món, B1–B2, T1–T4 | Đạt — `load_contract()` |
| `day_plan` D1–D5: ingredients = công thức × suất | Đạt — khớp bảng ticket |
| Quán độc lập dùng đủ menu (vd. `lau_mam`) | Đạt |
| Trong day chỉ order món thuộc kế hoạch | Đạt |
| Suất dự kiến không giới hạn số bán | Đạt (≥2 đơn khi plan=1 suất) |
| Hai đơn không tiêu trùng nguyên liệu (reserved) | Đạt — spawn → `no_dish` khi available=0 |
| 4 bàn bận → bỏ lượt spawn | Đạt |

API bàn giao TV4: `chonoi/day_plan.py` (`compute_ingredients`, `plan_for_day`); `QuanSim.plan_dishes` / `available_stock` / `try_spawn_customer`.

[Test](../../../tests/test_quan_plan_p2.py) · [spawn P1 vẫn xanh](../../../tests/test_quan_customers.py)
