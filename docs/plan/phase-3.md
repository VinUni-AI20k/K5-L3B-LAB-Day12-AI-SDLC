# Kế hoạch Phase 3 — Mùa Nước Nổi (`Test Contract v1.2`)

Thực hiện hành động đã chốt tại [Retro Phase 2](../retro.md): rà soát đầy đủ tác động schema trước khi sửa mô phỏng.

## Ma trận tác động chuyển sang kho cá thể `v1.2`

| Module | File cần đổi | Test bị ảnh hưởng (giữ / sửa / thêm) | Người phụ trách |
|---|---|---|---|
| Contract & Inventory | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py` | **Sửa:** `test_smoke_p1.py`, `test_gather_items.py` | TV3 (`Besoi2004`) |
| Scenario Validator | `chonoi/scenario.py` (`hold`, `stock`, `customers[].reserved`) | **Sửa:** `test_python_starter_units.py`, `test_quan_customers.py` | TV3 (`Besoi2004`) |
| Gather (`gather.py`) | `chonoi/sim/gather.py` (cấp ID `I*`, hao `-2`/tick, `spoiled`, `lost` LIFO) | **Sửa:** `test_gather_core_contract.py`, `test_gather_v11.py` · **Thêm:** `test_freshness_gather_v12.py` | TV3 (`Besoi2004`) |
| Adapter chuyển pha | `chonoi/sim/quan.py`, `chonoi/sim/day.py` (tương thích danh sách `stock`/`reserved` ngay ở Turn 4) | **Sửa:** `test_quan_service.py`, `test_day_shop_pause.py` | TV3 (`Besoi2004`) |
| Quán `v1.2` & Cháy (`burn`) | `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/contract.py`, `game.contract.json` | **Thêm:** `test_quan_v12_burn.py` | TV5 (`letuandat131`) |
| HUD & Release Notes | `chonoi/web/index.html`, `CHANGELOG.md`, `docs/verification/phase-3.md`, `docs/clarify.md` | Smoke 2 tiến trình & `--mode day` | TV5 (`letuandat131`) |
