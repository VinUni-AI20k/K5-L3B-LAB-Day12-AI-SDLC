# Ma trận truy vết Phase 2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả trên nhánh P2-03 |
|---|---|---|---|
| Ticket-02 §2, §4.1 và §4.5 · vòng ngày 1–5 | Smoke ca đầy đủ, kiểm thứ tự event và snapshot đổi pha | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.3 · kế hoạch và kho | Đối chiếu D1–D5, lọc thực đơn, test lại bàn giao kho qua hai tiến trình và mâu thuẫn khi mở quán | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.5 · Shop và trạng thái xuyên ngày | Chạy Giỏ → Quán → Shop với thao tác nấu, lấy món, phục vụ, trả tiền và mua oxy. Kiểm tra tiền, điểm và cấp áp dụng | [Test headless](../../tests/test_day.py) | Đạt |
| Ticket-02 §4.2 và §4.4 · pause | Pause Gather, Quán và Shop, kiểm tra đồng hồ, cạnh nút và lệnh mua | [Test headless](../../tests/test_day.py) | Đạt |
| Hồi quy Phase 1 và ghép cá bơi/sinh đàn P2-01 | Chạy toàn bộ test với preset v1.1, gồm luồng ngất → mở quán với kho rỗng và lịch sinh cá trong vòng ngày | [Kết quả chạy](../proof/phase-2/integration.md) | 129/129 test qua |

Cần chạy lại khi ghép phần hành vi Cá Sấu và giao diện vòng ngày. Bảng này ghi bằng chứng của P2-03 đã ghép với P2-01.
