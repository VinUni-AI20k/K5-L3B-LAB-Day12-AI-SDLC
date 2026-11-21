# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Q-P2-01: 2 Bếp nấu độc lập song song | Test 2 bếp B1, B2 nấu đồng thời, bắn `dish_ready` đúng tick | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-02: Ưu tiên nhận đơn theo order_tick cũ nhất | Test bếp trống tự động chọn đơn của khách có `order_tick` nhỏ nhất (nếu bằng thì `table_id` nhỏ hơn) | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-03: Ưu tiên tương tác gần nhất | Test phím E chọn đối tượng gần nhất; cùng khoảng cách ưu tiên Bếp trước Bàn $\rightarrow$ id | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-04: Menu 6 món Phase 2 | Test đọc menu động 6 món (kể cả món phức tạp `lau_mam`), nấu, bưng và phục vụ | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-05: Đóng ca dọn món | Test khi hết giờ ca (`quan_end`), dọn sạch món đang nấu/chín trên bếp và món trên tay | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |
| Q-P2-EXT: Mở rộng `burn` (Cháy món) | Test khi bật `burn_s: 20`, đĩa chín quá 1200 ticks chuyển sang `burned` (`dish_burned`), dọn bếp bằng phím tương tác | [`quan-2bep-test.txt`](docs/proof/phase-2/quan-2bep-test.txt) | đạt |

## Đánh giá ngắn
- **Yêu cầu đạt:**
  - Quán hỗ trợ linh hoạt 2 bếp và 4 bàn, điều phối đơn thông minh theo thứ tự thời gian đặt và ưu tiên khoảng cách.
  - Tương thích hoàn toàn menu 6 món và cấu trúc mở rộng của Phase 2.
  - Hoàn thành tính năng mở rộng `burn` (Cháy món) ngay trong module Quán mà không ảnh hưởng tới core engine.
