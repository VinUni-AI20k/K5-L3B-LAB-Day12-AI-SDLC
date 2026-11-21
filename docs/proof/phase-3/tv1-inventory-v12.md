# TV1 · Kiểm chứng schema kho cá thể v1.2, độ tươi & hợp đồng Phase 3 (`AC-P3-01`)

## 1. Unit & Adapter Test (`tests/test_inventory_v12.py`)

Lệnh chạy:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests/test_inventory_v12.py -v
```

Kết quả quan sát (`Ran 9 tests in 0.962s` — **OK**):
- `test_contract_has_freshness_and_validates_bounds`: `game.contract.json` chứa khối `tuning.freshness` chuẩn (`100, 0.5, 0.25, 30`); từ chối thiếu/thừa khóa, `bool`, `NaN`, `decay <= 0`, `spoiled_below >= initial`, và `contract_version` lạ.
- `test_v12_roundtrip_id_sort_and_atomic_write`: ghi file nguyên tử (không sót file `.tmp`), sắp theo `id_key` (`I2` trước `I10`), kho rỗng `{"items":[]}`, lỗi ghi không làm hỏng file cũ.
- `test_v12_rejects_invalid_schemas_and_keeps_v11_compatibility`: ở `1.1` vẫn đọc/ghi kho đếm; ở `1.2` từ chối kho đếm, trùng ID, ID rỗng/sai kiểu, kind lạ, `fresh` `bool`/`-0.1`/`100.1`/`NaN`/`Infinity`/`-Infinity`, thiếu/thừa khóa bằng `BadInput` (mã thoát `2`).
- `test_v12_sample_fixture_is_valid`: xác nhận [inventory.v12.sample.json](../../contracts/inventory.v12.sample.json) hợp lệ.
- `test_freshness_decay_threshold_30_and_roundtrip_precision`: `fresh=30` ươn ngay tick gather 1 (chỉ 1 lần); từ `100` tụt đến tick `8400` (gather) / `16800` (quan) giữ `30` chưa ươn, sang `8401` / `16801` mới ươn; bảo toàn lưới `1/240` qua ghi/đọc file JSON; giữ đúng nhánh với `30.0001` / `29.9999`.
- `test_decay_preserves_lifo_order_and_sorts_spoiled_by_id_key`: giữ nguyên thứ tự LIFO của `hold`, event `spoiled` trả theo `id_key`.
- `test_id_allocator_and_make_item_continue_after_deletion`: `IdAllocator.reserve_all` + `make_item` tiếp tục tăng `I11`, `I12` kể cả sau khi xóa cá thể.
- `test_selection_pricing_tip_and_cook_order`: chọn tươi nhất hòa theo `id_key`, bỏ qua hàng ươn, tính `floor(niêm yết × avg_fresh / 100)`, boa `floor(base_price × 0.2)`, sắp `cook_started.items` theo `(kind, id_key)`.
- `test_headless_cli_v11_inventory_still_works`: CLI `python -m chonoi.headless --mode quan --inventory ...` vẫn hoạt động trên `contract_version: "1.1"`.

## 2. Regression P1–P2 trên bản đang ở `contract_version: "1.1"`

Lệnh chạy:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests/test_python_starter_units.py tests/test_smoke_p1.py tests/test_gather_survival.py tests/test_gather_harvest.py tests/test_gather_monsters.py tests/test_gather_fish_p2.py tests/test_quan_customers.py tests/test_quan_kitchen.py tests/test_quan_plan_p2.py tests/test_day_cycle.py tests/test_phase1_gameplay.py tests/test_team_check.py
```

Kết quả quan sát: **88/88 test đạt (`OK`)** trong `18.451s`.
