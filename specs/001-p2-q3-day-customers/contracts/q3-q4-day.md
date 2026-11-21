# Đối chiếu Q3–Q4–Day sau merge

`docs/contracts/README.md` là đề xuất PO, chờ Integrator duyệt. Ticket-02 trong bảng được dẫn theo tài liệu đó, chưa được xác nhận độc lập. Main kiểm chứng `63f850e`.

| Yêu cầu/tài liệu | Code hoặc manifest hiện tại | Ảnh hưởng Q3 | Người sở hữu | Hành động đề xuất |
|---|---|---|---|---|
| DaySim truyền kho và menu_filter | Constructor nhận inventory/filter; chưa có DaySim | Chưa kiểm chuyển kho, reset ca | Bào | Triển khai Day và chạy day 1/3 ngày |
| Ticket-02: day_plan mảng 5 object | Manifest map 1–5; D2–D5 khác bảng ticket | Chưa chốt trích món và số lượng | Bào + Dương | Đối chiếu ticket gốc, xác nhận schema và giá trị |
| Quán toàn menu, Day lọc trước kho | None toàn menu, rỗng không món, ID lạ BadInput; số lượng chưa là hạn mức | Độc lập đã test, semantics số lượng còn mở | Bào + Dương | Chốt cách truyền dishes và ý nghĩa số |
| order_tick, table_id, dish_id, reservation | Khách mới tick đến, fixture mặc định 0, chặn số âm; ledger giữ/tiêu/nhả một lần | Hai bếp ưu tiên tick rồi table_id chuỗi; T2/T10 chưa xác nhận | Quốc + Kiên + Dương | Chốt thứ tự ID và fixture |
| Snapshot stock khả dụng theo giả định clarify #4 | Snapshot trừ reserved; kho vật lý trừ khi nấu | Hợp giả định, chưa là quyết định cuối | Quốc + Dương | Xác nhận và thống nhất giao diện Day |
| Event customer_arrived/customer_left theo đề xuất dùng order_id, left có reason/reputation; no_dish | Code dùng customer_id; left có dish_id, thiếu reason/reputation; không phát no_dish | Schema và điều kiện kết thúc chưa thống nhất | Dương + Bào | Chốt và đồng bộ các bên sau khi duyệt |
| State waiting/ordered/eating, khách rời khi nấu | Waiting và ordered đều giảm patience; món vẫn ready sau khách rời | Q4-F1; thiếu liên kết xác định khách–món | Kiên + Dương | Chốt chính sách, sau đó sửa và regression |

Không tự sửa contract. [Proof main](../../../docs/proof/phase-2/q3/postmerge-baseline-63f850e.txt). Patch Q4 `5dbdf13` là lịch sử; filter rỗng và kiểm order_tick âm đã có trên main, không áp lại patch.
