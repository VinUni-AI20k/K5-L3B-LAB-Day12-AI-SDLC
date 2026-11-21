# Nguồn và trạng thái sau merge

`docs/plan/phase-2.md` và `docs/plan/phan-chia-cong-viec.md` giao Quốc khách, bàn, filter và reservation; Kiên sở hữu bếp. Main `63f850e` có manifest v1.1, hai bếp, bốn bàn, sáu món. `docs/contracts/README.md` dẫn TICKET-02 nhưng ghi là đề xuất PO chờ Integrator duyệt; ticket gốc chưa được đối chiếu độc lập lần này.

PR #6 và #8 đã ghép Q3/Q4; filter rỗng và kiểm order_tick âm đã hiện diện, không áp lại patch lịch sử. Q4-F1 vẫn tái hiện; DaySim chưa có. Xem [bảng lệch](contracts/q3-q4-day.md) và [proof](../../docs/proof/phase-2/q3/postmerge-baseline-63f850e.txt). No_dish, event, state, kho và chính sách món mồ côi chờ xác nhận.
