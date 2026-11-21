# Kiểm chứng thiết lập Godot

- Godot 4.5.1 Standard trên Linux x86_64 tải scene chính và thoát thành công với `godot --headless --path godot --quit-after 5`.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` chạy đạt 32/32 test với quyền mở cổng localhost.
- Thao tác phím trong cửa sổ editor chưa được kiểm tra.
