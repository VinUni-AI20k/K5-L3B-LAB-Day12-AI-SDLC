# Changelog
## Unreleased
### Added
- Quán lát 4 (@minhthu27): `quan_service.py` — `tick_service` (bếp nấu → `dish_ready`, khách ăn xong → `paid` + boa + uy tín), `interact` (bếp trước bàn, `cook_started` / `dish_picked` / `served`).
- `tests/test_quan_service.py`: luồng nấu → bưng → phục vụ → trả tiền, thiếu nguyên liệu, ăn xong không boa, hết ca, cùng seed giống nhau.
### Changed
- `quan.py`: khách dựng từ scenario có mặc định `state`, `patience_ticks`, `eat_ticks`.
