# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| TV2 — chuyển vùng và oxy (PRD E/F) | `GatherCore` và `GatherCoreContract.test_oxygen_empty_payload_and_no_repeat` | [Chu trình oxy](../proof/phase-1/member-2/prd-correction/oxygen-cycle.jsonl), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: oxy theo vị trí cuối bước, đúng biên mặt nước, `oxygen_empty` có `oxygen_ticks:0` và không lặp. |
| TV2 — ngạt/ngất và payload LIFO (PRD E/F) | Test unit mốc ngạt/ưu tiên; `GatherCoreContract.test_faint_lost_lifo_and_empty_inventory` với giỏ rỗng và nguyên liệu trùng | [Phiên ngất](../proof/phase-1/member-2/prd-correction/faint.jsonl), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: choke tick 60/120/180; ngất có đủ `cause:choke,lost,hp:0`; `lost` đảo đúng giỏ trước khi xóa. |
| TV2 — giỏ/snapshot | `test_hold_capacity_reads_tuning_and_rejects_partial_yield`, thứ tự nhặt, snapshot độc lập và kiểm trần scenario | [Log mới](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: nhận đủ lô hoặc từ chối, không nhận một phần; snapshot player/hold giữ giá trị sau bước tiếp. Helper đã dùng trong đường hái/bắt TV3. |
| TV2 — kho ngất/cập bến (PRD G) | Test CLI ngất ghi đè kho cũ bằng rỗng; fixture cập bến | [Kho ngất](../proof/phase-1/member-2/prd-correction/faint.inventory.json), [kho bến](../proof/phase-1/member-2/prd-correction/dock.inventory.json) | Tôi xác nhận đạt: ngất ghi `items:{}`; cập bến giữ đúng 1 cá lóc, 2 bông súng. |
| TV2 — tất định/hồi quy | So byte hai phiên ngất; toàn suite + headless gather/quan 600 ticks | [Hash/payload](../proof/phase-1/member-2/prd-correction/summary.json), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: JSONL giống từng byte; 70/70 test qua; hai chế độ CLI thoát 0. |
| Hồ sơ đội | `python tools/check_team.py` | [Kết quả thực chạy](../proof/phase-1/member-2/prd-correction/summary.json) | Tôi ghi nhận chưa đạt: thành viên 6 còn placeholder; TV3–5 đã điền. |
| DoD toàn Phase 1 | Cần review các lát, HUD, hồ sơ nhóm và tag trên commit bàn giao main | [Báo cáo TV2](../proof/phase-1/member-2/README.md) | Tôi chưa kết luận toàn bộ Phase 1 đạt; lần hiệu chỉnh TV2 hiện nằm trên nhánh riêng. |
| Lát 2 · Hái nút ready gần nhất ở mặt nước, tính đúng mép bán kính, hòa theo id | `tests/test_gather_items.py::Harvest` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Giỏ thiếu chỗ → `hold_full`, nút giữ nguyên; dưới nước không hái | `Harvest.test_hold_full_keeps_node`, `test_no_harvest_under_water` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Bắt cá dưới nước, hòa theo id, hồi chiêu `catch_cooldown_s`; mặt nước không bắt | `tests/test_gather_items.py::Catch` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Thiếu chỗ khi bắt → `hold_full`, giữ đàn, không hồi chiêu, không thử đàn khác | `Catch.test_hold_full_no_cooldown_no_other_fish` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Cập bến ghi kho đúng giỏ; chạm `--ticks` trước khi xong thì không ghi kho | `tests/test_gather_items.py::DockInventory` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Smoke hai tiến trình: quán tick 0 có `stock {"bong_sung":2,"ca_loc":1}` | Lệnh smoke mục G PRD-0 (seed 42) | [catch.json](../proof/phase-1/gather-items/catch.json), [quan.jsonl](../proof/phase-1/gather-items/quan.jsonl) | đạt (trên nhánh lát 2, chưa có luật quán) |

## Đánh giá ngắn
- Tôi đã hiệu chỉnh Gather Core theo PRD-0 E/F/G và chạy 70 test sau tích hợp TV3–5. Kết quả test không thay thế kiểm chứng đầy đủ nghiệp vụ quán, HUD và DoD.
- Bằng chứng TV2 hiện hành nằm trong `member-2/prd-correction/`; log trước đó được giữ để truy vết. Integrator cần review nhánh sửa, nhóm hoàn thiện thông tin TV6 và kiểm chứng trên commit bàn giao trước tag.
