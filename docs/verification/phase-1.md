# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| TV2 — chuyển vùng và oxy | `GatherCore.test_dive_surface_use_end_position_and_emit_once`, `test_surface_boundary_refills_and_clamps_oxygen`, `test_oxygen_empty_only_on_positive_to_zero`, `test_oxygen_refill_reads_tuning` | [Chu trình oxy](../proof/phase-1/member-2/oxygen-cycle.jsonl), [log test](../proof/phase-1/member-2/commit-6-checks.txt) | Tôi xác nhận đạt trong phạm vi TV2: ngưỡng mặt nước tính cả dấu bằng; sự kiện chỉ phát khi chuyển trạng thái; oxy dựa trên vị trí cuối bước. |
| TV2 — ngạt và ngất | `GatherCore.test_choking_starts_on_tick_oxygen_reaches_zero`, `test_surface_resets_choking_before_damage`, `test_choke_interval_reads_tuning`, `test_faint_clears_hold_before_end_and_precedes_docking_and_time` | [Phiên ngất](../proof/phase-1/member-2/faint.jsonl) | Tôi xác nhận đạt: choke tại tick 60/120/180; tick 180 phát choke → faint → gather_end, giỏ rỗng. |
| TV2 — giỏ LIFO và snapshot | 4 test g?m `test_hold_*`, `test_snapshot_keeps_player_and_hold_values_after_next_step`, `test_scenario_accepts_full_hold_and_rejects_over_capacity` trong `GatherCore` | [Log 45 test](../proof/phase-1/member-2/commit-6-checks.txt) | Tôi xác nhận đạt với helper giỏ: giữ thứ tự nhặt, trả số món nhận thực tế, không vượt tuning, snapshot giữ dữ liệu player/hold sau bước tiếp theo. Hái/bắt cá chưa được tích hợp. |
| TV2 — kho khi ngất và hồi quy cập bến | `GatherCore.test_faint_writes_empty_inventory_through_runner`, fixture faint/dock và smoke tích hợp có sẵn | [Kho ngất](../proof/phase-1/member-2/faint.inventory.json), [kho cập bến](../proof/phase-1/member-2/dock.inventory.json) | Tôi xác nhận đạt: ngất xuất `items: {}`; cập bến giữ đúng 1 cá lóc và 2 bông súng. |
| TV2 — tất định và hồi quy | Chạy cùng fixture ngất hai lần, so byte; toàn suite + headless gather/quan 600 ticks | [Hash và sự kiện](../proof/phase-1/member-2/summary.json), [log](../proof/phase-1/member-2/commit-6-checks.txt) | Tôi xác nhận đạt: output ngất giống từng byte; 45/45 test qua; hai chế độ CLI thoát 0. |
| Hồ sơ đội | `python tools/check_team.py` | [Kết quả kiểm tra](../proof/phase-1/member-2/commit-6-checks.txt) | Tôi ghi nhận chưa đạt: GitHub handle của TV3–6 chưa điền. |
| Gather Items và toàn bộ Phase 1 | Cần kiểm thử hái/bắt cá sau lượt TV3 | [Bàn giao TV3](../proof/phase-1/member-2/README.md) | Tôi chưa xác nhận hoàn thành lát 2 hoặc toàn bộ Phase 1. |

## Đánh giá ngắn
- Tôi đã kiểm chứng Gather Core và các đường hồi quy sẵn có; chưa kết luận về cơ chế hái/bắt cá hay nghiệp vụ quán còn TODO.
- Tôi bàn giao helper giỏ và bằng chứng tái chạy cho TV3. Nhóm cần điền đủ TEAM.md, tích hợp lát 2 rồi kiểm chứng lại trước khi gắn tag phase-1.
