# Kiểm chứng Phase 2 — phần Q3

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
