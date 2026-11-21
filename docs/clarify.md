# Clarify — câu hỏi và câu trả lời (PO & Integrator ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 10:15 | Khi nhấn `interact` trong vùng bến tàu vừa có nút hái vừa trong bán kính bến thì ưu tiên cái nào? | Ưu tiên cập bến (`in_dock`) trước để kết thúc phiên và ghi nhận kho an toàn; chỉ khi ngoài bến mới xử lý hái nút bông. | Integrator |
| 2 | 2026-11-21 10:20 | Khách chọn món ở quán được giữ chỗ nguyên liệu (`reserved`) tại thời điểm nào? | Giữ chỗ ngay khi khách vào bàn và chọn món thành công; nhằm tránh việc khách sau tranh chấp nguyên liệu mà bếp chưa kịp nấu. | PO |
| 3 | 2026-11-21 10:25 | Khi Út Sen ngất do ngạt nước (`fainted`), giỏ hàng và file kho xử lý thế nào? | Khi ngất, toàn bộ đồ trong giỏ bị trôi mất (`hold = []`), phiên lặn kết thúc và file kho không được ghi hoặc ghi kho rỗng. | Integrator |
| 4 | 2026-11-21 (bàn giao TV2) | Nếu đàn cá cho nhiều món hơn chỗ trống của giỏ, lấy một phần hay từ chối cả đàn? | Tôi cung cấp helper giỏ trả số món thực nhận, tối đa bằng chỗ trống. Helper không quyết định xóa đàn cá hoặc phát event khi nhận thiếu. Tôi chuyển câu hỏi này cho PO/TV3 xác nhận trước khi tích hợp bắt cá; chưa coi đây là quyết định đã thống nhất. | Chờ PO/TV3 |
