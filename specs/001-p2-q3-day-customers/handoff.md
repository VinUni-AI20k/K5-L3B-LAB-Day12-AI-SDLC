# Bàn giao Q3 Phase 2 sau merge

Main `63f850e`; PR #8 merge `9f60259`, PR #6 và #10 đã merge. PR #8 không có review submission trong dữ liệu GitHub lúc kiểm; merge không chứng minh QA phê duyệt. GitHub Issues của repo đang tắt; chuyển nội dung sau qua kênh nhóm phù hợp.

- **Kiên (`ttkien0710`) + Dương (PO): Q4-F1.** Fixture `test_q4_f1_orphan_dish_reproduced`: C1 ở T1, một nguyên liệu cá lóc, patience 2; bắt đầu nấu, qua 2 tick khách rời, ép còn 1 tick nấu, món ready và nhấc được dù khách đã rời. Actual: món mồ côi. Expected cần PO/Kiên chốt: hủy, dùng lại hay chính sách khác. Test chứng minh tái hiện, không chứng minh sửa. Xác định liên kết khách/đơn/món, rồi thêm regression sau quyết định.
- **Bào (`invzble-z`):** DaySim thật nhận kho gather, truyền ID `day_plan.dishes` vào `QuanSim(..., menu_filter=...)`, reset ca, chạy headless day 1/3 ngày. Đối chiếu day_plan map/mảng và D2–D5, duyệt hợp đồng đề xuất.
- **Dương (`nganhduong123`):** chốt no_dish, bàn đầy/hết món, patience khi nấu, event customer_id/order_id, state, kế hoạch và Q4-F1; xác nhận ticket gốc.
- **Minh (`WorkOfMinh`):** QA trên commit tích hợp thực tế: Q3 P1/P2, Q4, hai bếp/reservation, lịch, sáu món, determinism, AC còn mở; xem [log](../../docs/proof/phase-2/q3/postmerge-baseline-63f850e.txt). PR merge không thay thế QA approval.

Chi tiết và người xử lý: [bảng lệch](contracts/q3-q4-day.md). Quốc tự xác nhận phản tư cá nhân; reviewer review PR hậu merge.
