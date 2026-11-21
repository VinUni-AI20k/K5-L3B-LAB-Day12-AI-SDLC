# Bàn giao Q3 Phase 2

- Bào: cần contract v1.1, `DaySim` truyền `menu_filter` theo plan và inventory vật lý; kiểm reset từng ca, snapshot và headless day. Test độc lập `test_each_new_shift_restarts_arrival_clock_and_copies_inventory` chưa thay thế integration Day thật.
- Kiên: review `docs/proof/phase-2/q3/q4-5dbdf13-proposed.patch` trên base `5dbdf13` (patch không có context: dùng `git apply --unidiff-zero` trong worktree riêng); xác nhận filter rỗng, `order_tick`, sort ID số, Q4-F1 và fixture nhiều khách cùng món. Patch chưa chỉnh chính sách Q4-F1.
- Minh: chạy QA sau ghép, kiểm Q3/Q4 hai bếp, schema và determinism v1.1; các log hiện tại là Q3 độc lập hoặc worktree đề xuất.
- PO: xác nhận no_dish, bàn đầy, kế hoạch hết món, order_tick fixture, patience khi nấu, stock snapshot và xử lý món mồ côi. Các lựa chọn tạm ở `research.md`, `docs/clarify.md`.

PR dự kiến: thêm menu_filter và order_tick cho khách; test lịch/bàn/menu/ledger và ghi nhận review Q4. Chạy 12 test P2, 23 P1 Q3 và full regression theo log. Dependency: contract v1.1/DaySim, hòa Q4 và PO; chưa đề xuất tag.
