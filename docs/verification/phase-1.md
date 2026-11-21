# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| **AC-P1-01** (Cấu hình repo & team) | Chạy `tools/check_team.py`, kiểm tra `TEAM.md` (5 người) và `game.contract.json` (`team_size: 5`) | [check-team.txt](../proof/phase-1/check-team.txt) | **Đạt** |
| **AC-P1-02** (Gather Lát 1: Oxy, ngạt, ngất xỉu) | `tests/test_gather_p1.py::GatherSlice1OxygenAndFaint` (kiểm tra ngạt ở đúng $t+59$, mất máu, ngất xóa sạch giỏ LIFO) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |
| **AC-P1-03** (Gather Lát 2: Hái rau & bắt cá) | `tests/test_gather_p1.py::GatherSlice2NodesAndFish` (kiểm tra thứ tự ưu tiên khoảng cách, cooldown, giỏ đầy không thể nhặt thêm) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |
| **AC-P1-04** (Bàn giao file kho) | `tests/test_integration_gather_quan.py` (cập bến ghi đúng file kho; ngất ghi kho rỗng `{items: {}}`) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |
| **AC-P1-05** (Quan Lát 3: Khách, giữ chỗ, kiên nhẫn) | `tests/test_quan_lat3.py` (khách theo lịch `phase_tick`, giữ chỗ nguyên liệu theo công thức, giảm kiên nhẫn, bỏ đi) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |
| **AC-P1-06** (Quan Lát 4: Bếp, phục vụ, tiền & uy tín) | `tests/test_quan_kitchen.py`, `tests/test_quan_service.py` (nấu, bưng, phục vụ, nhận tiền, tính boa & kẹp uy tín) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |
| **AC-P1-07** (Tính tất định từng byte - Determinism) | `python3 .agents/skills/verify-contract/verify.py` & `tests/test_qa_regression_p1.py` (chạy 2 lần cùng seed so sánh SHA-256 JSONL & Inventory) | [determinism.txt](../proof/phase-1/determinism.txt) | **Đạt** |
| **AC-P1-08** (Ràng buộc mã thoát & kịch bản) | `tests/test_qa_regression_p1.py::test_ac_p1_08_*`, `test_smoke_p1.py` (mã 0 khi hoàn thành, mã 2 khi mâu thuẫn/sai trường) | [test-suite.txt](../proof/phase-1/test-suite.txt) | **Đạt** |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:**
  - Toàn bộ 8 nhóm yêu cầu nghiệm thu (AC) của Phase 1 đều đã ĐẠT: 100 bài test trong bộ unit, integration và regression test suite chạy thành công (`OK (skipped=1)` do bỏ qua test mở socket trong sandbox).
  - Tính tất định từng byte đạt chuẩn tuyệt đối cho cả 2 chế độ `gather` và `quan`.
- **Điều cần chỉnh cho phase sau:**
  - Nhóm cần chú ý đồng bộ hợp đồng dữ liệu sớm hơn giữa các lát để tránh conflict khi merge nhánh.
  - Cần duy trì việc kiểm tra liên tục tính tất định và mã thoát `2` mỗi khi cập nhật logic game.
