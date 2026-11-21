# minhtriet061203 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Lát 3 `sim/quan` + `scenario.py` — khách đến theo lịch (`first_customer_tick`, mỗi `customer_interval_s`), bàn trống id nhỏ nhất, chọn món đều theo seed (luồng `customers`) trong món đủ kho khả dụng, `no_dish`, giữ chỗ nguyên liệu, kiên nhẫn → `customer_left patience` + uy tín kẹp, fixture `quan.customers` và kiểm mâu thuẫn (mã 2). Test: `tests/test_quan_customers.py` (22 test). Bằng chứng: `docs/proof/phase-1/lat3-quan-customers.txt`.
- Tôi đã review (kèm link): (điền khi review lát 4 của len2412)
- AI sai ở đâu và tôi phát hiện thế nào: AI viết lát 3 trước khi pull hợp đồng `docs/contracts/README.md` nên tự đặt tên trường (`order_state`, id đơn `O…`), luồng RNG và `data` sự kiện khác hợp đồng; khi pull về rebase thì phát hiện và sửa theo hợp đồng. Câu còn mở ghi `docs/clarify.md` #7–9. Máy Windows không có `python3` nên test hộp đen lỗi lúc đầu; chạy lại bằng shim `python3` thì xanh.
- Điều tôi học được: (tự điền)
