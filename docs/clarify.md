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
| 7 | 21/11 … | Thứ tự xử lý khách trong một bước quán (kiên nhẫn / khách mới)? | **Đã có trong PRD-0 mục F (Quán):** 1) đồng hồ, timer, nấu, ăn, giảm kiên nhẫn → 2) bếp → 3) di chuyển + tối đa 1 interact → 4) theo id bàn: ăn xong trả tiền, khách chờ kiên nhẫn 0 rời (còn giờ) hoặc rời `closing` (hết ca, không trừ uy tín), rồi `quan_end` → 5) còn giờ thì khách mới. Giả định cũ (rời ngay ở bước 1) **sai**, đã sửa: phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ. | PRD-0 (minhtriet061203 sửa code) |
| 8 | 21/11 … | Lịch khách tính theo gì khi scenario đặt `time_left_ticks`? | **Đã có trong PRD-0 mục D:** `phase_tick` bắt đầu từ 0, lịch khách tính theo `phase_tick` kể cả khi rút ngắn ca. Khớp code. | PRD-0 |
| 9 | 21/11 … | Khách đang ăn có giảm kiên nhẫn không? Uy tín cộng số thực có sai số? | Giả định (lát 3): chỉ khách `waiting` giảm kiên nhẫn. Uy tín làm tròn 6 chữ số sau mỗi lần đổi để `floor` không lệch (vd 2.8 + 0.2). | minhtriet061203 (chờ PO) |
| 10 | 21/11 … | (P2) 8 đàn đầu ca chọn thế nào? TICKET-02 chỉ ghi "Đầu ca 8 đàn ở 8 điểm khác nhau" và hướng "theo seed". | Giả định: lặp 8 lần đúng luật "Sinh cá" (trọng số loài chuẩn hóa trên loài còn điểm, điểm cách mọi đàn > 1 m nên 8 điểm khác nhau), hướng đều trong [0, 360), luồng RNG `fish_spawn`. Cài ở `GatherSim._spawn_school()`. | Integrator (nglngnguyen-gh) |
| 11 | 21/11 … | (P2) Khóa `recoil_dist` là quãng lùi mỗi bước hay tổng? | Giả định: tổng trong `recoil_ticks` = 2.0 m (mỗi bước 2/60 m, đúng TICKET-02 mục 1.2). | Integrator (nglngnguyen-gh) |
| 12 | 21/11 … | (P2) Ngưỡng độ sâu để quái phát hiện / chạm ("d ≥ 10" với Cá Sấu, "d < 8" với Rắn) lấy từ khóa nào? | Giả định: cận dưới `depths` của loài, không thêm khóa riêng. | Integrator (nglngnguyen-gh) |

## Giả định nhóm đã chốt (không cần hỏi, có căn cứ trong PRD)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| G1 | 21/11 … | Chọn món "đều theo seed" dùng luồng RNG nào? | Luồng riêng `Streams.get("customers")`, chọn đều trong danh sách món đủ nguyên liệu khả dụng đã sắp theo id món (mã Unicode). Căn cứ: PRD-0 mục E "chọn ngẫu nhiên nhất quán trong mỗi bản nộp", `AGENTS.md` (RNG chỉ qua `Streams`). | Integrator (nglngnguyen-gh) |
| G2 | 21/11 … | Id khách đặt theo quy tắc nào? | Tiền tố `C` (C1, C2…), cấp bằng `IdAllocator`, nối sau hậu tố lớn nhất đã nạp. `order_id` = id khách. Ghi trong `docs/contracts/README.md` mục 4. | Integrator (nglngnguyen-gh) |
