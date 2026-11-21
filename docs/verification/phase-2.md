# Kiểm chứng Phase 2 — phần Q3

## Tích hợp mới nhất — main `ba17f4d`, verification HEAD `5b79199`

DaySim đã được kiểm thử thật với QuanSim sau PR #12 và các cập nhật Gather/Phase 3 mới nhất. Xem [day integration](../proof/phase-2/q3/day-integration-5b79199.txt), [headless Day 1/3](../proof/phase-2/q3/day-headless-5b79199.txt), [regression](../proof/phase-2/q3/day-regression-5b79199.txt) và [findings/handoff](../proof/phase-2/q3/day-findings.md).

| Phạm vi | Bằng chứng | Kết quả |
|---|---|---|
| DaySim→QuanSim; kho Gather, filter không rỗng, reservation/consume/release, ngày mới | `tests/test_p2_q3_day_integration.py` | đạt với các hành vi được assertion |
| Kế hoạch rỗng | `test_empty_day_plan_is_an_empty_quan_filter`, `test_empty_day_plan_does_not_spawn_customer_for_unplanned_dish` | chưa đạt: `dishes={}` thành `menu_filter=None`, khách vẫn có thể nhận món |
| Reputation đầu ca và giữa ngày | `test_day_level_reputation_is_passed_into_first_quan_shift`, `test_reputation_earned_in_quan_survives_into_next_day` | chưa đạt: DaySim không truyền/khôi phục uy tín tích lũy |
| Pause | `test_sim_tick_stays_still_while_paused` | chưa đạt: `sim_tick` tăng cùng tick ngoài; `phase_tick`/timer gameplay đứng |
| Headless Day 1/3 + replay | `tests.test_p2_q3_day_integration.Q3DayHeadlessIntegrationTests` | đạt; mã 0, 1/1 và 3/3 ngày, replay byte-identical |
| Q4-F1 sau PR #12 | `tests.test_p2_q3.CustomersPhase2.test_q4_f1_orphan_dish_reproduced` | lỗi tái hiện; chính sách chưa được PO/Kiên duyệt |
| `no_dish` theo PO #11 | `tests.test_p2_q3_no_dish.NoDishTests` | đạt độc lập: no stock/recipe thiếu/filter rỗng phát một event mỗi lượt; bàn đầy và trước hạn im lặng; ca tiếp tục, không backlog hoặc cấp ID |
| Test suite | `day-regression-5b79199.txt` | 143 test, 5 expected failures, exit 0; Phase 1 verification 9/9 |

Do ba defect ở DaySim/Runner và Q4-F1/contract/QA còn mở, T07–T10 chưa thể đánh DONE. Bộ test sử dụng schema inventory v1.1; test Phase 3 hiện có vẫn chạy riêng để bảo vệ logic kho cá thể/giá tươi.

| Phạm vi | Bằng chứng | Trạng thái |
|---|---|---|
| Q3/Q4 sau merge main `63f850e` | [Log](../proof/phase-2/q3/postmerge-baseline-63f850e.txt) | Q3 P1 23, Q3 P2 12, Q4 7, regression 108; 9/9 bước, exit 0 |
| Q4-F1 | `tests/test_p2_q3.py::CustomersPhase2.test_q4_f1_orphan_dish_reproduced` | Tái hiện, chưa có chính sách được duyệt |
| Day và contract v1.1 | [Đối chiếu](../../specs/001-p2-q3-day-customers/contracts/q3-q4-day.md) | Manifest v1.1 có; Day chưa hỗ trợ, sai khác và hợp đồng chờ duyệt |
| Lịch sử Q3 | [Q3 proof](../proof/phase-2/q3/README.md) | Log 90/98/100 và patch worktree là kết quả trước merge |

# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Q-P2-01: 2 Bếp nấu độc lập song song | Test 2 bếp B1, B2 nấu đồng thời, bắn `dish_ready` đúng tick | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-02: Ưu tiên nhận đơn theo order_tick cũ nhất | Test bếp trống tự động chọn đơn của khách có `order_tick` nhỏ nhất (nếu bằng thì `table_id` nhỏ hơn) | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-03: Ưu tiên tương tác gần nhất | Test phím E chọn đối tượng gần nhất; cùng khoảng cách ưu tiên Bếp trước Bàn $\rightarrow$ id | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-04: Menu 6 món Phase 2 | Test đọc menu động 6 món (kể cả món phức tạp `lau_mam`), nấu, bưng và phục vụ | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-05: Đóng ca dọn món | Test khi hết giờ ca (`quan_end`), dọn sạch món đang nấu/chín trên bếp và món trên tay | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-EXT: Mở rộng `burn` (Cháy món) | Test khi bật `burn_s: 20`, đĩa chín quá 1200 ticks chuyển sang `burned` (`dish_burned`), dọn bếp bằng phím tương tác | [`quan-2bep-test.txt`](../proof/phase-2/quan-2bep-test.txt) | đạt |

## Đánh giá ngắn
- **Yêu cầu đạt:**
  - Quán hỗ trợ linh hoạt 2 bếp và 4 bàn, điều phối đơn thông minh theo thứ tự thời gian đặt và ưu tiên khoảng cách.
  - Tương thích hoàn toàn menu 6 món và cấu trúc mở rộng của Phase 2.
  - Hoàn thành tính năng mở rộng `burn` (Cháy món) ngay trong module Quán mà không ảnh hưởng tới core engine.
