# minhtriet061203 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Lát 3 `sim/quan` + `scenario.py` — khách đến theo lịch (`first_customer_tick`, mỗi `customer_interval_s`), bàn trống id nhỏ nhất, chọn món đều theo seed (luồng `quan_customer`) trong món đủ kho khả dụng, `no_dish`, giữ chỗ nguyên liệu, kiên nhẫn → `customer_left patience` + uy tín kẹp, fixture `quan.customers` và kiểm mâu thuẫn (mã 2). Test: `tests/test_quan_customers.py` (21 test). Bằng chứng: `docs/proof/phase-1/lat3-quan-customers.txt`.
- Tôi đã review (kèm link): (điền khi review lát 4 của len2412)
- AI sai ở đâu và tôi phát hiện thế nào: AI không đọc được nội dung PRD-0 trên lab board nên tên/`data` sự kiện là giả định — đã ghi `docs/clarify.md` #1–5 để PO xác nhận. Máy Windows không có `python3` nên test hộp đen lỗi lúc đầu; chạy lại bằng shim `python3` thì xanh.
- Điều tôi học được: (tự điền)
