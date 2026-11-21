# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| TV2-1 · Hái nút ở mặt nước, ưu tiên bến, hòa ID, regrow | `PYTHONPATH=tests:. python3 -m unittest tests/test_gather_harvest.py -v` (`test_harvest_*`, `test_dock_priority_over_harvest`) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV2-2 · Bắt cá dưới nước, cooldown, hòa ID, thiếu chỗ giữ nguyên cá & cooldown | `PYTHONPATH=tests:. python3 -m unittest tests/test_gather_harvest.py -v` (`test_catch_*`) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV2-3 · Bước cuối hái/cập bến, `tick_limit` giữ nguyên kho, smoke 2 tiến trình | `test_last_tick_harvest_and_dock_edge_and_tick_limit_inventory` + smoke Mục G (`gather` → `catch.json` → `quan` tick 0) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV4 · PRD-0 D–F, bếp → tay → bàn, boa, thu tiền và đóng ca | 6 test headless với khách fixture, đối chiếu tick, sự kiện, kho và điểm | [Kết quả TV4](../proof/phase-1/tv4-bep-thanh-toan.md) | Đạt trên cây làm việc |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
