# Ma trận truy vết Phase 3 (contract v1.2 — Mùa Nước Nổi)

Kết quả AC luật chạy tại `8073576` (p3/integ). Bằng chứng cuối cùng: [`docs/proof/phase-3/smoke-535972c/`](../proof/phase-3/smoke-535972c/summary.txt), `tools/smoke_p3.sh` trên main `535972c` (2026-11-21T06:59:39Z), 12/12 PASS, 233 test OK. Commit gắn tag chỉ thêm tài liệu so với 535972c.

| AC | Mô tả | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P3-D1 | DoD 1 — v1.2 bàn giao kho cá thể qua file và trong day; kho đếm → mã 2; id/độ tươi/ươn/giữ chỗ/giá/JSONL đúng luật | `tools/smoke_p3.sh` (threshold_spoiled_tick1, handoff_matches, counted_inventory_exit_2, day_runs) + AC-P3-01..24 | [summary.txt](../proof/phase-3/smoke-535972c/summary.txt) | đạt (535972c): smoke trên main 12/12 PASS |
| AC-P3-D2 | DoD 2 — HUD thấy độ tươi/hàng ươn; test qua ngưỡng, giữ lại khi vừa ươn, chốt giá, bàn giao | HUD: `tests/test_live.py` + kiểm tay; luật: AC-P3-02, 03, 13, 16, 17, 18 | [summary.txt](../proof/phase-3/smoke-535972c/summary.txt) | đạt phần test (8073576); HUD chờ kiểm tay trên trình duyệt |
| AC-P3-D3 | DoD 3 — ghi tác động, quyết định schema, thứ tự tích hợp; đóng góp từng người | `docs/plan/phase-3.md`; commit lát A–E, PR #16, sửa ghép 8073576 | [docs/plan/phase-3.md](../plan/phase-3.md) | đạt (8073576) |
| AC-P3-D4 | DoD 4 — CHANGELOG breaking change; regression P1–P3; test đổi có lý do; verification + bằng chứng khớp tag; clarify + ai-log | `CHANGELOG.md`; `PYTHONPATH=tests:. python3 -m unittest discover -s tests`; comment `# P3 [THAY THẾ]` | [summary.txt](../proof/phase-3/smoke-535972c/summary.txt) | đạt (535972c): regression 233/233, smoke trên main, CHANGELOG + comment P3 [THAY THẾ] |
| AC-P3-D5 | DoD 5 — mở rộng (current, reservations) | Nhóm 4 người không bắt buộc; không làm | — | không áp dụng |
| AC-P3-D6 | DoD 6 — tag phase-3 trên main | `git show phase-3` | — | chờ tag phase-3 vào commit merge chứa thư mục này |
| AC-P3-01 | Luật v1.2 — contract v12 | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_01_contract_v12` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-02 | Luật v1.2 — prd threshold fixture spoiled tick one exact data | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_02_prd_threshold_fixture_spoiled_tick_one_exact_data` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-03 | Luật v1.2 — gather file quan smoke preserves id kind fresh | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_03_gather_file_quan_smoke_preserves_id_kind_fresh` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-04 | Luật v1.2 — v11 count inventory rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_04_v11_count_inventory_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-05 | Luật v1.2 — wrong schema rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_05_wrong_schema_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-06 | Luật v1.2 — unknown kind rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_06_unknown_kind_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-07 | Luật v1.2 — duplicate id rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_07_duplicate_id_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-08 | Luật v1.2 — out of range or nonfinite fresh rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_08_out_of_range_or_nonfinite_fresh_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-09 | Luật v1.2 — empty inventory valid | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_09_empty_inventory_valid` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-10 | Luật v1.2 — gather decay per second | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_10_gather_decay_per_second` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-11 | Luật v1.2 — quan decay including reserved stock | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_11_quan_decay_including_reserved_stock` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-12 | Luật v1.2 — spoiled once in id order in each phase | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_12_spoiled_once_in_id_order_in_each_phase` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-13 | Luật v1.2 — threshold uses unrounded value | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_13_threshold_uses_unrounded_value` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-14 | Luật v1.2 — reserved ids freshest then numeric id | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_14_reserved_ids_freshest_then_numeric_id` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-15 | Luật v1.2 — explicit reserved id is consumed even if fresher exists | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_15_explicit_reserved_id_is_consumed_even_if_fresher_exists` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-16 | Luật v1.2 — spoiled reservation released and replaced before cook | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_16_spoiled_reservation_released_and_replaced_before_cook` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-17 | Luật v1.2 — spoiled reservation insufficient unfulfillable stays waiting | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_17_spoiled_reservation_insufficient_unfulfillable_stays_waiting` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-18 | Luật v1.2 — cook items kind then numeric id and mean fresh price | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_18_cook_items_kind_then_numeric_id_and_mean_fresh_price` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-19 | Luật v1.2 — tip on locked price through cook pick serve pay | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_19_tip_on_locked_price_through_cook_pick_serve_pay` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-20 | Luật v1.2 — day handoff same tick no extra decay and ids increase | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_20_day_handoff_same_tick_no_extra_decay_and_ids_increase` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-21 | Luật v1.2 — pause stops freshness resume decays once | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_21_pause_stops_freshness_resume_decays_once` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-22 | Luật v1.2 — replacing reservation releases entire recipe | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_22_replacing_reservation_releases_entire_recipe` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-23 | Luật v1.2 — affected orders reallocate in table id order | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_23_affected_orders_reallocate_in_table_id_order` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |
| AC-P3-24 | Luật v1.2 — conflicting or spoiled reserved ids rejected code two | `tests/test_fresh_p3.py::FreshP3::test_ac_p3_24_conflicting_or_spoiled_reserved_ids_rejected_code_two` | [test.log](../proof/phase-3/smoke-535972c/test.log) | đạt (8073576) |

## Đánh giá ngắn
- 24 AC luật (AC-P3-01..24, ánh xạ 1-1 tới test hộp đen `tests/test_fresh_p3.py`): 24 đạt, 0 chưa đạt.
- Regression P1–P3: 233 test OK. `tools/smoke_p3.sh` trên p3/integ: 12/12 PASS.
- D1, D4 đạt trên main 535972c. Còn chờ: kiểm tay HUD (D2), tag (D6). Không làm mở rộng (D5).
- Sự cố tích hợp: hai PR cùng sửa `chonoi/jsonl.py` (xuất fresh 6 chữ số), bản gộp gọi biến `key` không tồn tại → mọi headless crash, 121 test đỏ; sửa ở 8073576. Rút kinh nghiệm: file dùng chung chỉ một người sửa, người kia rebase.
