# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Quy trình: hỏi Anh Năm hàng xóm (tab Phase 1 trên lab board) → không trả lời được thì hỏi giảng viên hoặc nhóm tự đặt giả định → ghi vào bảng.
> Câu 1–6 đã hỏi Anh Năm trên lab board, nhận phản hồi `not_granted` (không trả lời được) → nhóm tự đặt giả định dưới đây. Nếu sau này giảng viên hoặc đề phase sau trả lời khác, sửa luật theo trả lời và ghi lại dòng mới.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11 … | Nhóm 5 người phải xong ≥ 1 mục **Mở rộng**. Danh sách mục gồm những gì, và hạn là phase 1 hay cả buổi lab? | Anh Năm: `not_granted`. Hạn: **cả buổi lab** (PRD-0 mục 2: "Kỳ vọng mở rộng tính cho cả buổi lab"). Giả định: phase 1 chỉ làm lõi; danh sách mục lấy từ lab board/PRD phase sau, PO chọn một mục gọn khi lõi đã xanh. | Nhóm (PO nglngnguyen-gh chốt) |
| 2 | 21/11 … | Đơn chuyển sang `unfulfillable` khi nào? PRD-0 mục D có trạng thái này nhưng mục F không có luật nào đặt nó (nguyên liệu được giữ ngay khi gọi). | Anh Năm: `not_granted`. Giả định: phase 1 không có luồng nào sinh `unfulfillable`. Chỉ nhận từ fixture và kiểm hợp lệ theo mục D (còn chờ, `reserved` rỗng, không có món ở bếp/tay), sai thì mã 2. | Nhóm (PO nglngnguyen-gh chốt) |
| 3 | 21/11 … | `customer_left.data.reputation` là uy tín **sau** khi cộng `left_reputation_delta` hay trước? | Anh Năm: `not_granted`. Giả định: uy tín **sau** khi cộng delta và kẹp [0, 5]. Với `closing` (không trừ) là uy tín hiện tại. | Nhóm (PO nglngnguyen-gh chốt) |
| 4 | 21/11 … | `paid.data.amount` có đúng bằng `base_price + tip` không? Trả lúc đóng ca (`closing`) thì boa tính thế nào? | Anh Năm: `not_granted`. Giả định: `amount = base_price + tip`. Boa là giá trị đã chốt lúc `served`, không tính lại khi trả lúc `closing`. | Nhóm (PO nglngnguyen-gh chốt) |
| 5 | 21/11 … | "Tỷ lệ kiên nhẫn còn lại sau bước 1" để tính boa tính thế nào, đúng bằng ngưỡng có được boa không? | Anh Năm: `not_granted`. Giả định: tỷ lệ = `patience_ticks_left / (patience_s × 60)` lấy sau bước 1 (sau khi giảm kiên nhẫn); `≥ tip_min_patience_ratio` thì boa, nên đúng 0.5 vẫn được boa (PRD dùng chữ "đạt"). | Nhóm (PO nglngnguyen-gh chốt) |
| 6 | 21/11 … | HUD hình khối của `chonoi.live` có đủ cho DoD "HUD đọc được trong lúc chơi" không? | Anh Năm: `not_granted`. Giả định: chưa đủ chắc chắn. Bổ sung nhãn chữ + số cho đủ các mục HUD ở PRD-0 mục 2. Sáng: thời gian, oxy, Máu, giỏ. Tối: kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín. Long (lát 2) làm sau khi xong luật. | Nhóm (PO nglngnguyen-gh chốt) |
| 7 | 21/11 … | Thứ tự xử lý khách trong một bước quán (kiên nhẫn / khách mới)? | Giả định (lát 3): đồng hồ → giảm kiên nhẫn, khách hết kiên nhẫn rời → [lát 4: nấu/ăn] → đi lại → [lát 4: interact] → khách mới theo lịch → hết ca. Khách rời và khách mới cùng tick thì bàn vừa trống được dùng ngay. | minhtriet061203 (chờ PO) |
| 8 | 21/11 … | Lịch khách tính theo gì khi scenario đặt `time_left_ticks`? | Giả định (lát 3): theo `phase_tick` của lượt chạy (0 ở đầu lượt, khớp `phase_tick` trong snapshot), không suy từ `time_left_ticks`. | minhtriet061203 (chờ PO) |
| 9 | 21/11 … | Khách đang ăn có giảm kiên nhẫn không? Uy tín cộng số thực có sai số? | Giả định (lát 3): chỉ khách `waiting` giảm kiên nhẫn. Uy tín làm tròn 6 chữ số sau mỗi lần đổi để `floor` không lệch (vd 2.8 + 0.2). | minhtriet061203 (chờ PO) |

## Giả định nhóm đã chốt (không cần hỏi, có căn cứ trong PRD)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| G1 | 21/11 … | Chọn món "đều theo seed" dùng luồng RNG nào? | Luồng riêng `Streams.get("customers")`, chọn đều trong danh sách món đủ nguyên liệu khả dụng đã sắp theo id món (mã Unicode). Căn cứ: PRD-0 mục E "chọn ngẫu nhiên nhất quán trong mỗi bản nộp", `AGENTS.md` (RNG chỉ qua `Streams`). | Integrator (nglngnguyen-gh) |
| G2 | 21/11 … | Id khách đặt theo quy tắc nào? | Tiền tố `C` (C1, C2…), cấp bằng `IdAllocator`, nối sau hậu tố lớn nhất đã nạp. `order_id` = id khách. Ghi trong `docs/contracts/README.md` mục 4. | Integrator (nglngnguyen-gh) |
