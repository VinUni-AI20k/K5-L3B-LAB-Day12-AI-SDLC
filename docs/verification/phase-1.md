# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Lát 2 · Hái nút ready gần nhất ở mặt nước, tính đúng mép bán kính, hòa theo id | `tests/test_gather_items.py::Harvest` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Giỏ thiếu chỗ → `hold_full`, nút giữ nguyên; dưới nước không hái | `Harvest.test_hold_full_keeps_node`, `test_no_harvest_under_water` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Bắt cá dưới nước, hòa theo id, hồi chiêu `catch_cooldown_s`; mặt nước không bắt | `tests/test_gather_items.py::Catch` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Thiếu chỗ khi bắt → `hold_full`, giữ đàn, không hồi chiêu, không thử đàn khác | `Catch.test_hold_full_no_cooldown_no_other_fish` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Lát 2 · Cập bến ghi kho đúng giỏ; chạm `--ticks` trước khi xong thì không ghi kho | `tests/test_gather_items.py::DockInventory` | [tests.txt](../proof/phase-1/gather-items/tests.txt) | đạt |
| Smoke hai tiến trình: quán tick 0 có `stock {"bong_sung":2,"ca_loc":1}` | Lệnh smoke mục G PRD-0 (seed 42) | [catch.json](../proof/phase-1/gather-items/catch.json), [quan.jsonl](../proof/phase-1/gather-items/quan.jsonl) | đạt (trên nhánh lát 2, chưa có luật quán) |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
