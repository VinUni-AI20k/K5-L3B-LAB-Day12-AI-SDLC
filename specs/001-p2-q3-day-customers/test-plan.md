> Sau merge: manifest v1.1 và Q3/Q4 đã có trên main; DaySim và phê duyệt hợp đồng còn mở. Xem [research](research.md), [handoff](handoff.md). Nội dung dưới là baseline lịch sử.

# Test plan

`tests/test_p2_q3.py` và `tests/test_p2_quoc.py`: boundary lịch, bàn, filter, sáu món giả lập, shortage, reservation, timeout, payment, dữ liệu fixture và seed. `tests/test_p1_q3.py` hồi quy Q3. `tests/test_p2_q3_day_integration.py` chạy DaySim/QuanSim thật: Gather→Quan kho đếm v1.1, filter, reservation/consume/release, lịch khách 120+900k, D1–D5 dạng map và list, đổi ngày, thanh toán, event, headless 1/3 ngày deterministic và pause.

Trên runtime HEAD `813b0b7`, được kiểm bởi test commit `053867b`, suite mới có 15 test: 10 đạt và 5 expected failure được giữ có chủ đích cho ba defect thuộc DaySim/Runner (filter rỗng, truyền/giữ reputation, `sim_tick` khi pause). Expected failure không được tính là AC đạt. Q4-F1 vẫn tái hiện trong `tests/test_p2_q3.py`; test này chỉ chứng minh lỗi tồn tại, không xác nhận chính sách.

Phase 3 test thật hiện có là `tests/test_p3_quan_price.py` (4 test); chạy cùng Q3/Q4/Day và toàn suite. [Kết quả và lệnh](../../docs/proof/phase-2/q3/day-regression-053867b.txt). Ticket-02 gốc không có trong checkout, vì vậy kiểm tra map/list không giải quyết xung đột contract hay xác nhận nội dung ticket.
