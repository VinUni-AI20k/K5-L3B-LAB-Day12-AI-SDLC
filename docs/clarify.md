# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | README + `tools/check_team.py` yêu cầu nhóm 4–6 người; nhóm G2026 hiện chỉ có 3 (chưa tìm thêm được). Có được làm 3 người không? | Tạm giả định được: `team_size = 3`, `check_team.py` báo đúng 1 lỗi "4–6 người" (CI chỉ cảnh báo, không chặn). Chờ giảng viên xác nhận; có thêm người thì cập nhật `TEAM.md` + `team_size`. | Khuê (chờ PO/giảng viên) |
| 2 | 2026-11-21 | Khách không có món: khi có bàn trống mà không món nào đủ nguyên liệu khả dụng và phát `no_dish`, khách có được tạo và ngồi vào bàn không, hay bàn vẫn trống và lượt khách đó bị bỏ? | CHƯA HỎI Anh Năm. Giả định tạm (đang code): không tạo khách, bàn vẫn trống, chỉ phát `no_dish {}`. | Khánh (PO) |
| 3 | 2026-11-21 | Đơn `unfulfillable`: khách chỉ gọi món nấu được và giữ chỗ ngay, vậy khi nào một đơn chuyển sang `unfulfillable`? Ở Phase 1 có xảy ra không, hay chỉ dùng trong scenario? | CHƯA HỎI Anh Năm. Giả định tạm: sim không tự sinh `unfulfillable`, chỉ nhận từ scenario; khách đó vẫn chờ rồi hết kiên nhẫn như bình thường. | Khánh (PO) |
| 4 | 2026-11-21 | `random_fish: true` ở Phase 1: có phải chỉ nghĩa là 6 đàn lấy đúng vị trí `fish_initial` trong tuning và đứng yên, không rải ngẫu nhiên theo seed? Nếu scenario có `fish[]` mà `random_fish` vẫn true thì chỉ dùng `fish[]` hay cộng thêm cá mặc định? | CHƯA HỎI Anh Năm. Giả định tạm (Phong, gather): 6 đàn đứng yên lấy từ tuning. | Khánh (PO) |
| 5 | 2026-11-21 | Bắt cá khi giỏ thiếu chỗ: PRD ghi "phát `hold_full`, giữ đàn và cooldown". Có phải không đặt hồi chiêu mới, tick sau bấm Space vẫn bắt được ngay? | CHƯA HỎI Anh Năm. Giả định tạm (Phong, gather): không đặt cooldown mới khi thiếu chỗ. | Khánh (PO) |
| 6 | 2026-11-21 | Ngưỡng boa: `patience_s = 60` tức 3600 tick. Nếu phục vụ khi `patience_ticks_left = 1800` (sau khi đã trừ ở bước 1), tỷ lệ đúng 0.5. Trường hợp này có boa không, tức là so `>= tip_min_patience_ratio`? | CHƯA HỎI Anh Năm. Giả định tạm (đang code, có test): đúng 0.5 vẫn có boa (so `>=`). | Khánh (PO) |

> Cách điền: sau khi hỏi Anh Năm, thay cột "Trả lời / giả định" bằng câu trả lời thật (ghi rõ "Anh Năm trả lời: ...") hoặc, nếu bot không trả lời được, ghi "Nhóm tự đặt giả định: ..." kèm lý do. Nếu câu trả lời khác giả định tạm thì báo người giữ module để sửa luật.
