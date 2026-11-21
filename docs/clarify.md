# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 13:20 | Lưu trữ độ tươi nội bộ thế nào để tránh sai số dấu phẩy động ở ngưỡng 30? | Dùng fractions.Fraction: fresh nạp từ str(v), hao mỗi tick = Fraction(quan_decay_per_s) / tick_hz, kẹp đáy 0. Cập nhật trực tiếp vào it['fresh'] để bếp đọc đúng. Chỉ đổi sang float làm tròn 3 chữ số khi xuất snapshot. | Nhóm League |
| 2 | 2026-11-21 13:20 | Thứ tự xử lý khi nhiều đơn cùng có phần giữ bị ươn trong một bước? | Xử lý tuần tự theo (order_tick, id bàn) bằng _re_reserve_v12; đơn xử lý trước lấy cá thể tươi nhất còn lại trong kho, không lấy cá thể mà đơn khác đang giữ. | Nhóm League |
| 3 | 2026-11-21 13:20 | Thứ tự id trong danh sách reserved của khách (kho v1.2)? | Sắp xếp theo độ tươi giảm dần (-fresh), hòa độ tươi thì ưu tiên id nhỏ hơn (id_key). | Nhóm League |

