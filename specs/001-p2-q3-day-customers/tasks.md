# Tasks Phase 2 Q3 — sau merge

- [x] T01 DONE — đối chiếu nguồn, Git, baseline.
- [x] T02 DONE — spec, đề xuất hợp đồng và test plan.
- [x] T03 DONE — kiểm bốn bàn, lịch, chọn món, reservation.
- [x] T04 DONE — menu_filter, order_tick và validation fixture; PR #8.
- [x] T05 DONE — Q3, regression, headless; [log](../../docs/proof/phase-2/q3/postmerge-baseline-63f850e.txt).
- [x] T06 DONE — review Q4 thật và bàn giao finding Q4-F1.
- [ ] T07 PARTIAL — DaySim đã chạy thật; kho Gather→Quan, filter khác rỗng, reservation/release/consume, lịch 120+900k, reset ca, D1–D5 map và list, headless 1/3 ngày được kiểm. Còn lỗi interface thuộc Bào: plan rỗng thành `None`, reputation không được chuyển/giữ, và `sim_tick` tăng khi pause. Xem [test tích hợp](../../tests/test_p2_q3_day_integration.py) và [findings](../../docs/proof/phase-2/q3/day-findings.md).
- [ ] T08 PARTIAL — Q3/Q4 và Phase 2–3 regression đạt; order priority, hai bếp, sáu món và reservation có test. Q4-F1 vẫn tái hiện trên HEAD `5b79199`; chính sách món mồ côi chưa được PO/Kiên duyệt.
- [x] T09a DONE — theo PO #11, `no_dish {}` phát đúng một lần ở mỗi lượt đến hạn khi còn bàn nhưng không có món khả thi; bàn đầy không phát event; không có backlog/ID cấp/đóng ca. [Test](../../tests/test_p2_q3_no_dish.py), [proof](../../docs/proof/phase-2/q3/no-dish.txt).
- [ ] T09b PARTIAL — manifest `day_plan` là mapping, tài liệu đề xuất mảng và D2–D5 khác; ticket gốc không có trong checkout. Tên event/state vẫn cần PO/Integrator đối chiếu nguồn chính thức.
- [ ] T10 PARTIAL — kỹ thuật đã có test và proof. QA review chính thức của Minh/reviewer chưa được ghi nhận; Quốc cần tự xác nhận phản tư.

Tổng: 6/10 DONE, 4 PARTIAL, 0 BLOCKED (60% DONE). PR merge và test tái hiện Q4-F1 không thay cho quyết định nghiệp vụ hoặc QA nghiệm thu.
