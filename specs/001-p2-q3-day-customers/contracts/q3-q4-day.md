# Bàn giao Q3–Q4–Day

`QuanSim(tuning, scenario, streams, ids, inventory=None, menu_filter=None)`: Day truyền các ID trong kế hoạch; `None` cho phép toàn menu, rỗng không cho món. Inventory là kho đếm vật lý. Mỗi ca tạo sim và elapsed tick mới. Q4 dùng `order_tick`, `table_id`, `reserved` và gọi `_consume_reservation` đúng một lần trước nấu. Q4 nhánh `8b3b93f` hiện trừ kho trực tiếp và sort chuỗi ID, cần hòa giải; không giả định đã tích hợp. Chính sách món sau khi khách rời đang mở (Q4-F1). Không xác nhận schema Day chính thức từ mock.
