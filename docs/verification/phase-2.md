# Ma trận truy vết Phase 2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả trên nhánh P2-03 |
|---|---|---|---|
| Ticket-02 §2, §4.1 và §4.5 · vòng ngày 1–5 | Smoke ca đầy đủ, kiểm thứ tự event và snapshot đổi pha | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.3 · kế hoạch và kho | Đối chiếu D1–D5, lọc thực đơn, test lại bàn giao kho qua hai tiến trình và mâu thuẫn khi mở quán | [Kết quả chạy](../proof/phase-2/integration.md) | Đạt |
| Ticket-02 §2 và §4.5 · Shop và trạng thái xuyên ngày | Chạy Giỏ → Quán → Shop với thao tác nấu, lấy món, phục vụ, trả tiền và mua oxy. Kiểm tra tiền, điểm và cấp áp dụng | [Test headless](../../tests/test_day.py) | Đạt |
| Ticket-02 §4.2 và §4.4 · pause | Pause Gather, Quán và Shop, kiểm tra đồng hồ, cạnh nút và lệnh mua | [Test headless](../../tests/test_day.py) | Đạt |
| Hồi quy Phase 1 | Chạy toàn bộ bộ test với preset v1.1 và kiểm thử phần bếp từ Người 4 | [Kết quả chạy](../proof/phase-2/integration.md) | 85/85 test qua |

Cần ghi lại kết quả trên commit bàn giao của nhóm sau khi tích hợp phần Gather và giao diện. Bảng này ghi bằng chứng cho P2-03.
