---
name: inventory-validator
description: Kiểm định file kho nguyên liệu theo chuẩn Contract G (buổi sáng sang buổi tối) và phân tích khả năng nấu các món trong menu.
---

# Skill: inventory-validator (Kiểm định File Kho)

## Khi nào dùng
- Sử dụng sau khi chạy buổi sáng (`gather`) để kiểm tra file kho xuất ra có hợp lệ trước khi đưa vào buổi tối (`quan`).
- Sử dụng để phát hiện sớm các lỗi sai schema (nguyên liệu lạ, số lượng âm, chứa số 0) trước khi chạy test.

## Lệnh thực thi
```bash
python .agents/skills/inventory-validator/validate_inventory.py docs/contracts/inventory.sample.json
```

## Kết quả đầu ra
1. Kiểm tra cấu trúc `{"items": {...}}` chuẩn Contract G.
2. Kiểm tra kiểu dữ liệu số nguyên dương và tên nguyên liệu hợp lệ.
3. Phân tích số suất món ăn tối đa quán có thể phục vụ được.
