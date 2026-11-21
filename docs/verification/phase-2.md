# Ma trận kiểm chứng Phase 2 — phần chur04

Các mã L3/L4 dưới đây là nhóm kiểm chứng nội bộ theo mục TICKET-02, không phải mã AC do giảng viên cấp. Kết quả thuộc working tree trên nhánh cá nhân, chưa phải commit bàn giao/tag của toàn nhóm.

| Phạm vi / mục ticket | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| L4 / 4.1–4.2: inputs, days, buy theo frame, boolean/cạnh lên, cờ sai mã 2 | Inputs11, HeadlessDay | [tests.txt](../proof/phase-2/chur04/tests.txt) | Đạt các trường hợp đã kiểm |
| L4 / 2, 4.4–4.5: đổi pha cùng tick, phase_tick=0, event phase/day cũ/mới, đóng Shop mới hoàn thành Ngày | DayAndShop + smoke CLI hai Ngày | [day-run1.txt](../proof/phase-2/chur04/day-run1.txt) | Đạt trên fixture v1.1 |
| L4 / 2: Shop oxygen/hp, đúng giá, max/funds/unknown, cấp áp từ Ngày kế, giữ earned/điểm | DayAndShop | [tests.txt](../proof/phase-2/chur04/tests.txt) | Đạt |
| L4 / 4.2: pause trước hành động, freeze timer/lịch, resume bước đó, không lặp cạnh/buy | DayAndShop: paused Shop, gather/quan, deadline nấu/ăn/kiên nhẫn, tick_limit paused | [tests.txt](../proof/phase-2/chur04/tests.txt) | Đạt |
| L3 / 1.3, 2: 2 bếp/4 bàn/6 món, ghế id nhỏ nhất, menu theo kế hoạch, không giới hạn suất dự kiến | Quan11 + ca 4 khách | [tests.txt](../proof/phase-2/chur04/tests.txt) | Đạt trên dữ liệu fixture |
| L4 / 4.3: tiền/cấp/plan sai, cấm stock/reputation; kiểm món fixture khi mở quán trên kho thực | DayAndShop | [tests.txt](../proof/phase-2/chur04/tests.txt) | Đạt các tình huống của lát day |
| Tích hợp kho: gather → inventory → quan | Hai tiến trình thật trong workspace v1.1 tạm | [inventory.json](../proof/phase-2/chur04/inventory.json), [quan](../proof/phase-2/chur04/integration-quan.txt) | Đạt với 4 nguyên liệu P1 trong ca mẫu |
| Tất định và giới hạn 22.200 tick / ≤20s | Hai CLI day cùng seed/input; một ca đủ thời lượng với random_fish=false | [summary.json](../proof/phase-2/chur04/summary.json), [full-day.log](../proof/phase-2/chur04/full-day.log) | Đạt trong fixture backend; chưa đo engine cá/quái mới |
| Mở rộng burn | Biên 1200/1201, thiếu hàng, giữ lại và nấu lại cùng tick | Quan11 | [tests.txt](../proof/phase-2/chur04/tests.txt) | Logic/test đạt; chưa bật manifest |
| Regression sau merge | 70 test gốc + 34 test mới | [tests.txt](../proof/phase-2/chur04/tests.txt) | 104/104 đạt, launcher Python cục bộ trên Windows |
| DoD toàn nhóm: manifest chung 1.1, cá/quái, 6 loại file kho, UI/FPS, tag | Chờ các lát tương ứng và kiểm lại trên main | [Giới hạn bàn giao](../proof/phase-2/chur04/README.md) | Chưa xác nhận |
