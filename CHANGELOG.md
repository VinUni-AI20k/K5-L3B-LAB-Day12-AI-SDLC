# Changelog
## Unreleased
### Added
- Quán lát 4 (@minhthu27): `quan_service.py` — `tick_service` (bếp nấu -> `dish_ready`, khách ăn đếm ngược), `interact` (bếp trước bàn: `cook_started` / `dish_picked` / `served`), `settle` (`paid`, boa, uy tín, rời bàn; hết ca trả hết rồi `quan_end`).
- `tests/test_quan_service.py`: 8 test hộp đen (nấu đến trả tiền, thiếu nguyên liệu, đơn unfulfillable, không boa, phục vụ nhầm khách, hết ca, cùng seed).
### Changed
- `quan.py`: thứ tự bước theo `docs/contracts/customer.md` mục 5; khách scenario có mặc định và `reserved` cấp theo công thức; `hand` là `{order_id, dish_id, base_price}`.
