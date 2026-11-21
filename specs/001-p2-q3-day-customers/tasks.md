# Tasks Phase 2 Q3

- [x] T01 Đối chiếu nhánh, nguồn, baseline và công việc đang có.
- [x] T02 Tạo spec, contract đề xuất và test plan; phân biệt nguồn chính thức.
- [x] T03 Kiểm bốn bàn, lịch, chọn món và reservation bằng tuning giả lập.
- [x] T04 Cung cấp `menu_filter`, `order_tick` và kiểm input fixture.
- [x] T05 Chạy test Q3, regression P1, headless P1 và kiểm tính tất định; lưu proof.
- [x] T06 Review Q4 thực tế và bàn giao khác biệt ledger, order và Q4-F1.
- [ ] T07 Tích hợp DaySim và chạy headless day với v1.1 chính thức (chờ integrator).
- [ ] T08 Hòa Q4 Phase 2 và kiểm hai bếp, thứ tự đơn cùng tick trên code ghép thật (chờ Q4/integrator).
- [ ] T09 PO xác nhận no_dish, mapping AC và quy tắc kế hoạch/khách (thiếu Ticket-02).
- [ ] T10 Quốc xác nhận phản ánh cá nhân; tích hợp và reviewer nghiệm thu.

T01–T06 là kết quả nội bộ, không phải nghiệm thu chính thức. Truy vết: US1 → T03 → `_spawn_customers` → `test_p2_quoc`; US2 → T04 → `_eligible_dishes` → `test_p2_q3`; US3 → T03 → reservation helpers → `test_p1_q3`, `test_p2_q3`; US4 → T06–T09 → `contracts/q3-q4-day.md` và proof.
