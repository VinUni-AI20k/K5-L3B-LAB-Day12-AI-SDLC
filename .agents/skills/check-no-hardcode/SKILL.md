---
name: check-no-hardcode
description: Kiểm tra luật mô phỏng không hard-code số tuning ngoài game.contract.json. Dùng sau khi sửa chonoi/sim/ và trước khi mở PR.
---

# check-no-hardcode

Công cụ dùng AST để quét các file Python trong `chonoi/sim/`, tìm literal số đáng ngờ chưa lấy từ tuning trong `game.contract.json`.

## Khi nào dùng
- Sau khi sửa luật trong `chonoi/sim/`.
- Trước khi mở PR.
- Khi thêm tuning mới hoặc phát hiện luật dùng số chưa có trong contract.

## Cách chạy
```text
python3 tools/check_no_hardcode.py
```

## Đọc kết quả
- Thoát mã `0`: không tìm thấy literal số đáng ngờ.
- Thoát mã `1`: có literal cần xem lại hoặc checker không đọc/quét được đầu vào; chẩn đoán được in kèm file và dòng.

Giá trị đã khai báo trong `game.contract.json`, hằng số cấu trúc phổ biến, annotation và dòng có `# allow-hardcode` được bỏ qua. Nếu phát hiện số tuning bị hard-code, chuyển luật sang đọc contract thay vì sửa test để bỏ qua.
