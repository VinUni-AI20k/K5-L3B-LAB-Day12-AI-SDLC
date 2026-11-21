---
name: quan-sim
description: Chuyên gia mô phỏng chế độ Mở Quán Ăn Chợ Nổi (quan)
---

# Quan Sim Skill

Dùng khi triển khai hoặc sửa đổi logic mở quán, đón khách, nấu bếp và thanh toán trong `chonoi/sim/quan.py`.

## Nguyên tắc:
1. Quản lý kho: tính kho khả dụng `available_stock = current_stock - sum(reserved)`.
2. Khách đến theo chu kỳ `customer_interval_s`, chỉ nhận bàn nếu còn món nấu được từ kho khả dụng. Khóa tạm nguyên liệu vào `reserved`.
3. Kiên nhẫn giảm dần; chạm 0 thì bỏ về (`customer_left`), trừ uy tín và giải phóng nguyên liệu giữ chỗ.
4. Bếp nấu đếm thời gian `cook_s`; món chín bưng phục vụ bàn tương ứng; khách ăn trong `eat_s` rồi thanh toán + tiền tip nếu phục vụ nhanh.
5. Hết ca tính toán tổng doanh thu và uy tín cuối cùng.
