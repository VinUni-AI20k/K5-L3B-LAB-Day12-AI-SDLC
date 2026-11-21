# Kiểm chứng Phase 2

| Phạm vi | Bằng chứng | Trạng thái |
|---|---|---|
| Q3 lịch, bốn bàn, menu/filter, reservation | [Q3 proof](../proof/phase-2/q3/README.md); `tests/test_p2_q3.py`, `tests/test_p2_quoc.py` | 10 test đạt trên tuning giả lập; chưa nghiệm thu v1.1 |
| Q3/Q4 hai bếp và Q4-F1 | `tests/test_p2_q3.py` | Code hiện tại không tiêu thụ reservation hai lần; Q4-F1 tái hiện, chờ chủ Q4 quyết định |
| Regression P1 | [Log](../proof/phase-2/q3/regression-headless.txt) | 98 test và 9/9 bước đạt, exit 0 |
| Day và contract v1.1 | Chưa có DaySim/contract v1.1 | Chưa chạy; chờ integrator |
| Rà soát Q4 5dbdf13 | [Patch và log đề xuất](../proof/phase-2/q3/q4-5dbdf13-proposed-tests.txt) | Trước patch 2/17 test lỗi; sau patch 19/19 đạt trong worktree tách biệt; Q4-F1 vẫn tái hiện, chưa ghép |
| Kiểm lại Q3 | [Regression hiện tại](../proof/phase-2/q3/current-verification.txt), `current-p2-tests.txt`, `current-p1-q3-tests.txt` | 100 test, 9/9 bước; Q3 P2 12 test, Q3 P1 23 test, exit 0 |

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
