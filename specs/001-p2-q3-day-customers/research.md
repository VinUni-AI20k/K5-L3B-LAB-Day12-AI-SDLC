# Nguồn và trạng thái sau merge

`docs/plan/phase-2.md` và `docs/plan/phan-chia-cong-viec.md` giao Quốc khách, bàn, filter và reservation; Kiên sở hữu bếp; Bào sở hữu DaySim/Runner. Main kiểm chứng mới `813b0b7` có manifest v1.1, hai bếp, bốn bàn, sáu món và DaySim. `docs/contracts/README.md` là đề xuất PO chờ Integrator duyệt. Ticket-02/Test Contract gốc không có trong checkout; GitHub issue search cũng không tìm thấy nguồn chính thức.

PR #6, #8, #10, #11, #12 đã ghép Q3/Q4/Phase 3; filter rỗng và kiểm order_tick âm đã có, không áp patch lịch sử. DaySim thật được kiểm thử. Kho bàn giao, reservation, lịch khách, ngày mới, payment, event order và headless Day smoke đạt trong scenario; ba lỗi DaySim/Runner còn mở. Q4-F1 vẫn tái hiện. Xem [bảng lệch](contracts/q3-q4-day.md), [proof](../../docs/proof/phase-2/q3/day-regression-053867b.txt) và [findings](../../docs/proof/phase-2/q3/day-findings.md). `no_dish`, event/state, nguồn ticket và chính sách món mồ côi chờ xác nhận.
