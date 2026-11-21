# QA Phase 3 · báo cáo tự động (`python3 tools/qa_p3.py`)

- Commit: `66aa5fc (+ thay đổi chưa commit)`
- Chế độ chạy CP1–CP7: **bản sao tạm bật 1.2 (manifest repo đang 1.1)**
- Máy đo: macOS-26.5.2-arm64-arm-64bit-Mach-O · Python 3.13.9
- Thời điểm: 2026-11-21 12:06:52

| CP | AC | Kiểm tra | Kết quả | Chi tiết |
|---|---|---|---|---|
| CP1 | AC-P3-02 | Giỏ fresh 30 → spoiled đúng tick 1, một lần | **PASS** | [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled", "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}] |
| CP2 | AC-P3-01/05 | gather --inventory-out → quan --inventory --ticks 0 (id/kind/fresh) | **PASS** | file (đủ chính xác)=[{'id': 'I1', 'kind': 'ca_linh', 'fresh': 99.99166666666666}, {'id': 'I2', 'kind': 'ca_loc', 'fresh': 57.49166666666667}] · gather_end=[{'id': 'I1', 'kind': 'ca_linh', 'fresh': 99.992}, {'id': 'I2', 'kind': 'ca_loc', 'fresh': 57.492}] · stock quán @0=[{'id': 'I1', 'kind': 'ca_linh', 'fresh': 99.992}, {'id': 'I2', 'kind': 'ca_loc', 'fresh': 57.492}] |
| CP3 | AC-P3-01 | v1.2 trả mã 2 cho kho đếm / sai schema | **PASS** | kho đếm v1.1→2 · id trùng→2 · kind lạ→2 · fresh 100.1→2 · fresh âm→2 · thiếu fresh→2 · fresh NaN→2 |
| CP4 | AC-P3-03 | Phần giữ vừa ươn → spoiled, giữ lại I2; không đủ → unfulfillable | **PASS** | có I2: reserved=['I2'] reserved · chỉ I1: reserved=[] unfulfillable |
| CP5 | AC-P3-04 | Hao 60 bước ở quán (50.25 → 50) rồi nấu: floor(60 × 50/100) = 30 | **PASS** | {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "items": [{"id": "I1", "kind": "ca_loc", "fresh": 50}], "base_price": 30} |
| CP6 | AC-P3-05 | Day: bàn giao cùng tick, pause/Shop không hao, id Ngày 2 cấp mới | **PASS** | bàn giao=True (tick 1) · pause 40 snapshot đứng=True · Shop 600 snapshot đứng=True · hold D2=[('I3', 'ca_loc', 100.0), ('I4', 'bong_sung', 80.0)] |
| CP7 | AC-P3-05 | Tất định day v1.2 (seed 7, 3.000 tick × 2) | **PASS** | sha256 ed086137f861a572 / ed086137f861a572 |
| CP8a | AC-P3-06 | Regression trên manifest repo (1.1) | **PASS** | Ran 124 tests in 9.969s · OK |
| CP8b | AC-P3-06 | Toàn suite khi bật 1.2 (bản sao) | **INFO** | Ran 124 tests in 10.503s · FAILED (failures=17, errors=1) · test còn dùng fixture kho đếm cần chủ lát đổi: test_catch_fish_underwater_cooldown_and_tie_break (test_gather_harvest), test_catch_hold_full_keeps_fish_and_cooldown_and_no_fallback (test_gather_harvest), test_choke_ignores_invulnerability_and_keeps_hold (test_gather_monsters), test_contract_has_six_dishes_two_stoves_four_tables (test_quan_plan_p2), test_dock_priority_over_harvest (test_gather_harvest), test_fainting_preempts_docking_and_timeout_and_exports_empty_inventory (test_gather_survival), test_harvest_hold_full_keeps_node_ready (test_gather_harvest), test_harvest_node_at_surface_and_edge_radius (test_gather_harvest), test_headless_cli_v11_inventory_still_works (test_inventory_v12), test_hit_tie_lifo_and_recoil (test_gather_monsters), test_inv_01_gather_writes_inventory_quan_reads_it (test_smoke_p1), test_keo_neo_and_ca_keo_integration_to_quan (test_gather_fish_p2), test_last_tick_harvest_and_dock_edge_and_tick_limit_inventory (test_gather_harvest), test_monster_faint_loses_remainder_and_saves_empty_stock (test_gather_monsters), test_one_day_default_waits_for_shop_timeout (test_day_cycle), test_plan_override_faint_and_dish_filter (test_day_cycle), test_session_steps_gather_and_dock (test_python_starter_units), test_time_ends_gather_and_keeps_hold (test_smoke_p1) |
