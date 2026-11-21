# Kiểm chứng ghép UI với mô phỏng

Nhánh `ui/cho-noi-hud` ghép luật chơi từ `main` tại commit `089e6d1`.

- Bộ test hiện có đạt 49/49. Phiên test Windows dùng `python.exe` cho lệnh headless và bật UTF-8.
- Kiểm tra dữ liệu live với vị trí dựng sẵn. Ở đàn F1, nhấn bắt phát sự kiện `fish_caught` với số lượng 3 và vị trí `[15, 5]`. Ở cây N1, nhấn tương tác bắt đầu bộ đếm mọc lại.
- Kiểm tra ca quán với `work/quan-ui-demo.json`. Bếp B1 chuyển sang chín, mục tiêu tương tác báo lấy món, tay nhận đúng món, rồi bàn T1 báo phục vụ và hành động phát sự kiện `served`.
- Với kho trống, sự kiện `no_dish` cho phép giao diện hiện thiếu nguyên liệu của một món gần đủ nhất.
- Luồng `--continue-quan` chỉ mở sau khi buổi sáng kết thúc. Đã kiểm tra chuyển kho sang quán trên cùng phiên và khởi động lại từ buổi sáng bằng R.

Chạy demo từ thư mục repo:

```powershell
python -X utf8 -m chonoi.live --mode gather --continue-quan --port 8012
```

Nhấn E ở bến để kết thúc buổi sáng, rồi nhấn E lần nữa ở bảng tổng kết để mở quán.

Sau lượt rà soát phần mở quán, bộ test đạt 51/51. Hai test mới kiểm tra gợi ý bắt đầu nấu, cảnh báo thiếu nguyên liệu vẫn còn sau thời gian hiển thị cũ và từ chối scenario có bếp đang nấu nhưng thiếu thông tin món.

Sau khi đồng bộ cấu hình Phase 2 từ `main` (`bf82d91`), 12 test tập trung vào quán và các bản sửa mới đều qua. Bộ đầy đủ trên nhánh UI có 35/51 test qua. Bản `main` cùng commit có 33/49 test qua, với cùng 16 test lỗi. Cấu hình buổi sáng khai `fish_initial` là số nguyên, trong khi `GatherSim` hiện cần danh sách. Hai test mới về quán đều qua sau đồng bộ.

`chonoi/live.py` bổ sung gợi ý tương tác, vị trí thu thập và thông tin thiếu nguyên liệu cho API trình duyệt. Các hàm chọn mục tiêu dùng chung với mô phỏng. Các trường hỗ trợ UI nằm trong dữ liệu live để giữ schema và payload của headless.
