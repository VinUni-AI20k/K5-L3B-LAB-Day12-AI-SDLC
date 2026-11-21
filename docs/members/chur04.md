# chur04 — Vũ Văn Chủ — Phase 1

- Phần việc đã thực hiện với Codex: lát 4 bếp → bưng → phục vụ → thanh toán, tiền/boa/uy tín, dọn đơn/đóng ca; nối `QuanSim.step`, bổ sung 28 test và [bằng chứng](../proof/phase-1/chur04-service.md). Vai PO: đối chiếu PRD-0 người dùng cung cấp, trả lời 8 câu trong [clarify](../clarify.md).
- Commit: thay đổi đang ở working tree nhánh `feat/quan-service-phase-1-chur04`; chưa có commit mới để dẫn link. Yêu cầu ≥3 commit có nội dung tính trong cả buổi lab, chưa xác nhận hoàn thành.
- Review: Codex đã rà code, thứ tự event, payload và test; chưa có review chéo của thành viên nhóm, cần cập nhật link sau khi thực hiện.
- AI sai ở đâu: helper tạo customer trong test ban đầu truyền trùng `dish_id`, gây TypeError; sửa helper để trường fixture ghi đè mặc định. Bộ test chạy lại đạt. Lỗi `python3` trên Windows được tách khỏi lỗi luật, không đổi assertion để làm xanh.
- Điều học được để tự xác nhận: timer và tương tác cùng tick quyết định deadline; phải giữ `order_id` cùng món, chốt boa lúc phục vụ và chỉ thu tiền/cộng uy tín sau đó.
