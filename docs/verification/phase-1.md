# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01: Smoke & Unit Tests Cơ sở | Chạy test suite toàn diện (`37/37 tests pass`) | [baseline_test.txt](docs/proof/phase-1/baseline_test.txt) | ĐẠT |
| AC-P1-02: Tính tất định Byte-by-Byte (Determinism) | Chạy tool `check_determinism.py` trên 2 lần chạy độc lập | [determinism_baseline.txt](docs/proof/phase-1/determinism_baseline.txt) | ĐẠT |
| AC-P1-03: Kiểm tra CLI & Bắt lỗi tham số (Exit Code = 2) | Chạy `tests/test_qa_determinism.py` phủ các ca tham số sai | [baseline_test.txt](docs/proof/phase-1/baseline_test.txt#L24-L26) | ĐẠT |
| AC-P1-04: Tích hợp Hợp đồng Kho (Gather xuất -> Quán nạp) | Chạy `Integration.test_inv_01_gather_writes_inventory_quan_reads_it` | [baseline_test.txt](docs/proof/phase-1/baseline_test.txt#L35-L37) | ĐẠT |
| AC-P1-05: Kiểm tra danh sách thành viên (TEAM.md) | Chạy `tools/check_team.py` qua `test_team_check.py` | [baseline_test.txt](docs/proof/phase-1/baseline_test.txt#L56-L59) | ĐẠT |

## Đánh giá ngắn
- **Yêu cầu nào đạt**: Khung kiểm thử tự động, tính tất định byte-by-byte (cả Gather và Quán), kiểm tra mã lỗi CLI và tính hợp lệ hợp đồng kho đều đạt 100%.
- **Yêu cầu chưa đạt**: Các luật chi tiết nâng cao (lặn ngạt, hái hoa, bắt cá, khách vào ăn) đang chờ Người 1 và Người 2 hoàn thiện logic trong sim.
- **Điều cần chỉnh cho phase sau**: Duy trì chạy tool `check_determinism.py` sau mỗi Pull Request merge vào `main`.
