# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| TV2 — chuyển vùng và oxy (PRD E/F) | `GatherCore` và `GatherCoreContract.test_oxygen_empty_payload_and_no_repeat` | [Chu trình oxy](../proof/phase-1/member-2/prd-correction/oxygen-cycle.jsonl), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: oxy theo vị trí cuối bước, đúng biên mặt nước, `oxygen_empty` có `oxygen_ticks:0` và không lặp. |
| TV2 — ngạt/ngất và payload LIFO (PRD E/F) | Test unit mốc ngạt/ưu tiên; `GatherCoreContract.test_faint_lost_lifo_and_empty_inventory` với giỏ rỗng và nguyên liệu trùng | [Phiên ngất](../proof/phase-1/member-2/prd-correction/faint.jsonl), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: choke tick 60/120/180; ngất có đủ `cause:choke,lost,hp:0`; `lost` đảo đúng giỏ trước khi xóa. |
| TV2 — giỏ/snapshot | `test_hold_capacity_reads_tuning_and_rejects_partial_yield`, thứ tự nhặt, snapshot độc lập và kiểm trần scenario | [Log mới](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: nhận đủ lô hoặc từ chối, không nhận một phần; snapshot player/hold giữ giá trị sau bước tiếp. Helper đã dùng trong đường hái/bắt TV3. |
| TV2 — kho ngất/cập bến (PRD G) | Test CLI ngất ghi đè kho cũ bằng rỗng; fixture cập bến | [Kho ngất](../proof/phase-1/member-2/prd-correction/faint.inventory.json), [kho bến](../proof/phase-1/member-2/prd-correction/dock.inventory.json) | Tôi xác nhận đạt: ngất ghi `items:{}`; cập bến giữ đúng 1 cá lóc, 2 bông súng. |
| TV2 — tất định/hồi quy | So byte hai phiên ngất; toàn suite + headless gather/quan 600 ticks | [Hash/payload](../proof/phase-1/member-2/prd-correction/summary.json), [log](../proof/phase-1/member-2/prd-correction/checks.txt) | Tôi xác nhận đạt: JSONL giống từng byte; 70/70 test qua; hai chế độ CLI thoát 0. |
| Hồ sơ đội | `python tools/check_team.py` | [TEAM.md](../../TEAM.md) | Đạt 6/6 sau khi TV4 bổ sung Đỗ Thanh Mai (`Laurent2526`). |
| TV4 — Quán theo PRD-0 | Test khách và phục vụ, chạy CLI với fixture cũ, kiểm tra payload và tính tất định | [Bằng chứng TV4](#kiểm-chứng-tv4), [ADR 0002](../adr/0002-quan-prd0-payloads.md) | 73/73 test qua. Hai chế độ headless thoát 0. |
| DoD toàn Phase 1 | Review luật Quán và thử HUD trên trình duyệt trước khi chốt bản bàn giao | [Phạm vi thay đổi](../adr/0002-quan-prd0-payloads.md) | Chờ Integrator review và gắn tag sau khi tích hợp vào `main`. |
| Lát 2 · Hái nút ready gần nhất ở mặt nước, tính đúng mép bán kính, hòa theo id | `tests/test_gather_items.py::Harvest` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Giỏ thiếu chỗ → `hold_full`, nút giữ nguyên; dưới nước không hái | `Harvest.test_hold_full_keeps_node`, `test_no_harvest_under_water` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Bắt cá dưới nước, hòa theo id, hồi chiêu `catch_cooldown_s`; mặt nước không bắt | `tests/test_gather_items.py::Catch` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Thiếu chỗ khi bắt → `hold_full`, giữ đàn, không hồi chiêu, không thử đàn khác | `Catch.test_hold_full_no_cooldown_no_other_fish` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Cập bến ghi kho đúng giỏ; chạm `--ticks` trước khi xong thì không ghi kho | `tests/test_gather_items.py::DockInventory` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Smoke hai tiến trình: quán tick 0 có `stock {"bong_sung":2,"ca_loc":1}` | Lệnh smoke mục G PRD-0 (seed 42) | [catch.json](../proof/phase-1/gather-items/catch.json), [quan.jsonl](../proof/phase-1/gather-items/quan.jsonl) | đạt (trên nhánh lát 2, chưa có luật quán) |

## Ghi chú kiểm chứng TV2
- Tôi đã hiệu chỉnh Gather Core theo PRD-0 E/F/G và chạy 70 test sau tích hợp TV3–5. Kết quả test không thay thế kiểm chứng đầy đủ nghiệp vụ quán, HUD và DoD.
- Bằng chứng TV2 nằm trong `member-2/prd-correction/`. Hồ sơ TV6 đã được hoàn thiện ở lượt TV4.

## Kiểm chứng TV4

| Kiểm tra | Kết quả trên nhánh `fix/hnib1908-phase1-quan-prd0` |
|---|---|
| Bộ test repo, gồm `test_quan_customers.py` và `test_quan_service.py` | 73/73 qua trên Windows với Python 3.13.9. Test bao phủ thứ tự tick, giữ chỗ, chọn đúng đơn, tip làm tròn xuống, tương tác gần nhất và đóng ca. |
| Headless `gather` và `quan`, seed 1 | Các lượt 120 và 600 tick thoát 0. Hai lượt 600 tick của mỗi chế độ cho JSONL giống từng byte. |
| [Fixture cùng tick của Phase 2](../proof/phase-2/member-4/same-tick.scenario.json) | Tick 120 phát `customer_left` cho C9 rồi `customer_arrived` cho C10. Uy tín còn 2,5. Hai lần chạy cho SHA-256 `8b1c554a9c09104b107b9544b2f2434669e6ee3701a39254ef9cd77f8fb803d8`. |
| Scenario cần giữ chỗ với `--inventory` rỗng | CLI thoát 2 trước khi tạo JSONL. |
| Live HTTP với bếp có món chín | Trang HTML và `/state` trả về bình thường. Snapshot chứa món dạng object với `order_id`, `dish_id` và `base_price`. Kiểm tra hiển thị trên trình duyệt còn chờ review. |

Chạy lại trên PowerShell với `python3` trên `PATH` để các test gọi được lệnh headless trong contract. Lượt kiểm chứng này dùng launcher `python3.exe` tạm từ Python trên máy.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python -m unittest discover -s tests -q
python tools/check_team.py
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out "$env:TEMP/chonoi-tv4-gather.jsonl"
python -m chonoi.headless --mode quan --seed 1 --ticks 600 --out "$env:TEMP/chonoi-tv4-quan.jsonl"
python -m chonoi.headless --mode quan --seed 1 --ticks 121 --snapshot-every 120 --scenario docs/proof/phase-2/member-4/same-tick.scenario.json --out "$env:TEMP/chonoi-tv4-same-tick.jsonl"
Get-FileHash "$env:TEMP/chonoi-tv4-same-tick.jsonl" -Algorithm SHA256
```
