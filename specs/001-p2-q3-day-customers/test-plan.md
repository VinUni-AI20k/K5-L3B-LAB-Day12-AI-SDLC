> Sau merge: manifest v1.1 và Q3/Q4 đã có trên main; DaySim và phê duyệt hợp đồng còn mở. Xem [research](research.md), [handoff](handoff.md). Nội dung dưới là baseline lịch sử.

# Test plan

`tests/test_p2_q3.py` và `tests/test_p2_quoc.py`: boundary lịch, bàn, filter, sáu món giả lập, shortage, reservation, timeout, payment, dữ liệu fixture và seed. `tests/test_p1_q3.py` hồi quy Q3. `phase-1-verification` chạy toàn suite, headless hai mode, byte determinism và bad input. Day và tuning v1.1 chính thức chưa chạy được. Q4 nhánh riêng cần tích hợp thật, không dùng test double để tuyên bố đạt.
