---
name: check-scenario
description: Kiểm tra tính hợp lệ của kịch bản scenario và file kho trước khi nạp vào runner headless hoặc live mode.
---

# Skill: check-scenario

## Khi nào dùng
Dùng khi thiết lập hoặc kiểm thử các kịch bản tùy biến (scenario JSON) và file kho (`inventory.json`), nhằm phát hiện sớm các lỗi miền giá trị (mã thoát 2) theo quy định của Test Contract.

## Các tiêu chí kiểm tra bắt buộc
1. **Scenario khối chế độ:** Chạy `--mode gather` chỉ được chứa khối `"gather"`, chạy `--mode quan` chỉ được chứa khối `"quan"`.
2. **Tọa độ thực thể:** Phải nằm hoàn toàn trong vùng biên `bounds` được quy định tại `game.contract.json`.
3. **Mặt nước & Độ sâu:** Nút hái bông phải ở mặt nước (`d = 0`). Đàn cá phải ở dưới nước (`d > surface_depth`).
4. **Sức chứa giỏ khoang:** Số lượng phần tử trong mảng `hold` không được vượt quá `hold_capacity` (12).
5. **Định dạng file kho:** Chỉ có khóa gốc `"items"`, số lượng nguyên liệu phải là số nguyên không âm (`>= 0`).
