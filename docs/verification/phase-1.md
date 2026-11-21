# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| **AC-P1-01**: Bơi, lặn tiêu oxy, nổi hồi oxy, ngạt trừ máu, hết máu ngất | Chạy kịch bản lặn dưới nước, kiểm tra giảm oxy; khi oxy về 0 đếm 60 tick phát `choke`; hết máu phát `faint` và xóa giỏ | [test_phase1_gameplay.py](../../tests/test_phase1_gameplay.py) · [test_suite.log](../proof/phase-1/test_suite.log) | **Đạt** |
| **AC-P1-02**: Hái hoa mặt nước, lặn bắt cá, kiểm tra sức chứa giỏ | Chạy kịch bản gần nút cây N1 nhấn interact -> `gather`; gần cá F1 nhấn catch -> `fish_caught` yield=3 | [test_phase1_gameplay.py](../../tests/test_phase1_gameplay.py) · [test_suite.log](../proof/phase-1/test_suite.log) | **Đạt** |
| **AC-P1-03**: Cập bến xuất kho và quán nhận đúng kho (Smoke mục G) | Ca sáng cập bến mang 2 bông súng, 1 cá lóc xuất file `catch.json`; ca tối đọc kho tick 0 nhận đúng stock | [dock.json](../proof/phase-1/dock.json) · [catch.json](../proof/phase-1/catch.json) · [quan.jsonl](../proof/phase-1/quan.jsonl) | **Đạt** |
| **AC-P1-04**: Quán nấu, phục vụ khách, tính tiền, boa và uy tín | Khách gọi món -> Bếp nấu `cook_started` -> Món chín `dish_ready` -> Bưng `dish_picked` -> Phục vụ `served` -> Ăn xong trả tiền `paid` | [test_phase1_gameplay.py](../../tests/test_phase1_gameplay.py) · [test_suite.log](../proof/phase-1/test_suite.log) | **Đạt** |
| **AC-P1-05**: Tính tất định (Deterministic byte-for-byte) | Chạy 2 lần cùng seed=7 và input, so sánh byte-by-byte bằng lệnh `cmp` | [det_run1.jsonl](../proof/phase-1/det_run1.jsonl) · [det_run2.jsonl](../proof/phase-1/det_run2.jsonl) · [determinism.txt](../proof/phase-1/determinism.txt) | **Đạt** |
| **AC-P1-06**: Bộ test tự động của starter | Chạy toàn bộ smoke test hộp đen theo Test Contract v1.0 | [test_smoke_p1.py](../../tests/test_smoke_p1.py) · [test_suite.log](../proof/phase-1/test_suite.log) | **Đạt** |
| TV1 · Bơi, lặn/nổi, oxy, ngạt (`choke`), ngất (`faint`), bỏ giỏ LIFO và xuất kho rỗng | `PYTHONPATH=tests;. python -m unittest tests/test_gather_survival.py -v` (3 ca headless theo PRD-0 mục F) | [tv1-gather-survival.md](../proof/phase-1/tv1-gather-survival.md) | đạt (3/3 test pass) |
| TV2-1 · Hái nút ở mặt nước, ưu tiên bến, hòa ID, regrow | `PYTHONPATH=tests:. python3 -m unittest tests/test_gather_harvest.py -v` (`test_harvest_*`, `test_dock_priority_over_harvest`) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV2-2 · Bắt cá dưới nước, cooldown, hòa ID, thiếu chỗ giữ nguyên cá & cooldown | `PYTHONPATH=tests:. python3 -m unittest tests/test_gather_harvest.py -v` (`test_catch_*`) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV2-3 · Bước cuối hái/cập bến, `tick_limit` giữ nguyên kho, smoke 2 tiến trình | `test_last_tick_harvest_and_dock_edge_and_tick_limit_inventory` + smoke Mục G (`gather` → `catch.json` → `quan` tick 0) | [tv2-gather.txt](../proof/phase-1/tv2-gather.txt) | đạt |
| TV4 · PRD-0 D–F, bếp → tay → bàn, boa, thu tiền và đóng ca | 6 test headless với khách fixture, đối chiếu tick, sự kiện, kho và điểm | [Kết quả TV4](../proof/phase-1/tv4-bep-thanh-toan.md) | Đạt trên cây làm việc |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:** Toàn bộ 6 AC của Phase 1 đã hoàn thành đầy đủ, logic mô phỏng cả hai ca sáng (gather) và tối (quan) hoạt động chính xác theo Test Contract v1.0.
- **Điều cần chỉnh cho phase sau:** Tối ưu hóa thêm phần render đồ họa động trên web canvas ở Phase 2 khi có sinh vật di chuyển và thêm món mới.
