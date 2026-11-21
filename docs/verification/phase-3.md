# Kiểm chứng Phase 3 — P3-02

PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests` — **152/152 test đạt, exit 0**. [Output thật](../proof/phase-3/inventory-v12-test.txt).

| AC | Test / bằng chứng | Trạng thái |
|---|---|---|
| AC-P3-I2-01 | `test_id_registry_observes_and_never_reuses`, `test_dropped_item_ids_are_not_reused_by_next_catch`, `test_day_registry_continues_after_handoff_and_resets_hold` | Đạt |
| AC-P3-I2-02 | `test_schema_accepts_six_kinds_and_clones`, `test_schema_rejects_old_counts_and_invalid_fields`, `test_headless_rejects_bad_file_before_output_with_exit_two` | Đạt |
| AC-P3-I2-03 | `test_atomic_write_replaces_file_and_cleans_temporary` và hồi quy `tick_limit` trong `test_gather_collection.py` | Đạt |
| AC-P3-I2-04 | `test_scenario_validates_individual_hold_and_stock`, các ca CLI sai schema trả 2 trước output | Đạt |
| AC-P3-I2-05 | `test_two_process_handoff_preserves_id_and_fresh`, `test_day_registry_continues_after_handoff_and_resets_hold` | Đạt ở adapter P3-02; hao tươi theo tick và chọn cá thể khi nấu thuộc P3-01/P3-03. |
| AC-P3-I2-06 | `game.contract.json` v1.2; toàn suite 152 test, gồm hồi quy Phase 1/2 | Đạt |

Các kỳ vọng test Phase 1/2 liên quan file kho, `gather_end.inventory` và snapshot Day đã đổi từ object đếm sang mảng cá thể theo Test Contract v1.2; luật di chuyển, cá, quái và bếp vẫn được kiểm trong toàn suite. Kho đếm chỉ còn là adapter nội bộ cho Quán và fixture cũ, không được nhận qua `--inventory`.
