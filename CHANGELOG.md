# Changelog
## Unreleased
### Added
- Quán lát 4 (@minhthu27): `quan_service.py` — `tick_service` (bếp nấu -> `dish_ready`, khách ăn đếm ngược), `interact` (bếp trước bàn: `cook_started` / `dish_picked` / `served`), `settle` (`paid`, boa, uy tín, rời bàn; hết ca trả hết rồi `quan_end`).
- `tests/test_quan_service.py`: 8 test hộp đen (nấu đến trả tiền, thiếu nguyên liệu, đơn unfulfillable, không boa, phục vụ nhầm khách, hết ca, cùng seed).
### Changed
- Ghép lát 4 với `quan_customers` (lát 3): dùng `build_fixture_customers`, `remove_customer`, `phase_tick`; món ở bếp và trên tay là payload `{order_id, dish_id, base_price}`.
- Sự kiện lát 4 đổi theo PRD/QA: `served` `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}`, `paid` `{order_id, table_id, base_price, tip, amount, reason}`, `cook_started`/`dish_ready`/`dish_picked` `{stove_id, order_id, dish_id}`.
- `quan.py`: thứ tự bước theo `docs/contracts/customer.md` mục 5; khách scenario có mặc định và `reserved` cấp theo công thức; `hand` là `{order_id, dish_id, base_price}`.
