# Báo cáo Kiểm Chứng Tự Động — Phase 1
Thời gian thực hiện: `2026-11-21 11:37:47`

## 1. Kết quả Unit Tests (Hồi quy)
- **Trạng thái:** ✅ ĐẠT (PASS) — `1.41s`
```text
test_ac_m2_01_gather_surface_node_success (test_gather_m2.GatherM2.test_ac_m2_01_gather_surface_node_success)
AC-M2-01: Hái nút mặt nước thành công. ... ok
test_ac_m2_02_node_regrown_event (test_gather_m2.GatherM2.test_ac_m2_02_node_regrown_event)
AC-M2-02: Nút mọc lại phát event node_regrown. ... ok
test_ac_m2_03_hold_full_on_gather (test_gather_m2.GatherM2.test_ac_m2_03_hold_full_on_gather)
AC-M2-03: Giỏ đầy khi hái phát event hold_full. ... ok
test_ac_m2_04_dock_priority_over_gather (test_gather_m2.GatherM2.test_ac_m2_04_dock_priority_over_gather)
AC-M2-04: Ưu tiên cập bến trước hái khi trong dock. ... ok
test_ac_m2_05_underwater_cannot_gather_surface_nodes (test_gather_m2.GatherM2.test_ac_m2_05_underwater_cannot_gather_surface_nodes)
AC-M2-05: Ở dưới nước không hái được nút mặt nước. ... ok
test_ac_m2_06_catch_fish_success (test_gather_m2.GatherM2.test_ac_m2_06_catch_fish_success)
AC-M2-06: Bắt đàn cá dưới nước thành công. ... ok
test_ac_m2_07_hold_full_on_catch (test_gather_m2.GatherM2.test_ac_m2_07_hold_full_on_catch)
AC-M2-07: Bắt cá thiếu chỗ phát event hold_full, giữ đàn cá, không hồi chiêu. ... ok
test_ac_m2_08_surface_or_cd_cannot_catch (test_gather_m2.GatherM2.test_ac_m2_08_surface_or_cd_cannot_catch)
AC-M2-08: Ở mặt nước hoặc đang cooldown thì không bắt cá. ... ok
test_ac_m2_09_tie_break_smallest_id (test_gather_m2.GatherM2.test_ac_m2_09_tie_break_smallest_id)
AC-M2-09: Khi bằng khoảng cách, chọn ID nhỏ nhất. ... ok
test_ac_m2_10_inventory_output_file (test_gather_m2.GatherM2.test_ac_m2_10_inventory_output_file)
AC-M2-10: Ghi file kho đúng format, sắp xếp key, bỏ count 0. ... ok

----------------------------------------------------------------------
Ran 10 tests in 1.264s

OK

```

## 2. Kết quả Mô phỏng Headless
### Chế độ: `docs/proof/phase-1/gather_seed1_ticks600.jsonl`
- **Proof:** [`docs/proof/phase-1/gather_seed1_ticks600.jsonl`](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-1/gather_seed1_ticks600.jsonl)
- **Trạng thái:** ✅ PASS (exit `0`, `0.12s`)
- **Snapshots:** `61` | **Events:** `0`
- **Thống kê sự kiện:**
```json
{}
```


## 3. Gợi ý điền ma trận kiểm chứng (docs/verification/phase-1.md)
| AC / Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Unit tests hồi quy | unittest discover | [verification_summary.md](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-1/verification_summary.md) | Đạt |
| Mô phỏng `docs/proof/phase-1/gather_seed1_ticks600.jsonl` | Headless (61 snapshots) | [docs/proof/phase-1/gather_seed1_ticks600.jsonl](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-1/gather_seed1_ticks600.jsonl) | Đạt |
