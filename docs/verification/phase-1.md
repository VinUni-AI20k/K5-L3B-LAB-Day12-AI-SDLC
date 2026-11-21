# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Q4: Bếp nấu và dish_ready | Unit test `test_stove_cooks_to_ready` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |
| Q4: Tương tác nấu và nhấc món (cook_started, dish_picked) | Unit test `test_interact_cook_started_and_pick` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |
| Q4: Phục vụ bàn và khách ăn trả tiền (served, paid, tip 20%, reputation) | Unit test `test_serve_and_paid_with_tip` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |
| Q4: Phục vụ trễ không nhận được tip | Unit test `test_paid_without_tip_when_patience_low` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |
| Q4: Thứ tự ưu tiên interact (gần nhất, bếp trước bàn) | Unit test `test_interact_priority_stove_before_table` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |
| Q4: Hết ca tối phát sự kiện quan_end | Unit test `test_shift_ends_with_quan_end` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | Đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Lát 4 (bếp nấu, phục vụ, tiền, uy tín) hoàn thành 100%, 7/7 unit tests đạt.
- Điều cần chỉnh cho phase sau: Tích hợp với Lát 3 (sinh khách ngẫu nhiên theo lịch) khi Lát 3 hoàn thành.
