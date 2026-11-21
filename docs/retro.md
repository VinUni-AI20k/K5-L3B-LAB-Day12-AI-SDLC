# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: test luật và smoke tích hợp chạy được sớm; bằng chứng tất định (cùng seed, cùng từng byte).
- Điều tệ: phần luật và phần giao diện không được chốt thứ tự sớm, nên `index.html` có nhiều lần conflict khi merge.
- 1 hành động cho Phase 3: merge `main` thường xuyên (mỗi lát xong) để conflict nhỏ và sớm.

## Phase 3
- Điều tốt: đổi kho sang cá thể có danh sách lát và hợp đồng v1.2 rõ ràng; bảng truy vết AC-P3 có test đi kèm.
- Điều tệ: hai bản cùng làm một việc (chế độ tương phản cao, benchmark) mà không báo nhau, nên phải giải thủ công.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm một phần. Có merge `main` nhiều lần, nhưng vẫn còn conflict trên `index.html` (ba lần).
- Điều tốt: bằng chứng benchmark ba lần, regression 189 test OK, soak 10 Ngày có artifact, clone sạch đã kiểm trên Windows.
- Điều tệ: `bench_cmd` từng trỏ tới bản headless, không đo hình; chưa thống nhất sớm; soak bot không điều khiển người chơi.
- Số liệu commit trên nhánh chính (theo tên tác giả, chưa đối chiếu GitHub): huydn8816 24, vindpd203 14, Bảo khoảng 9, khanhdev 4.
- Một lần AI sai và cách nhóm phát hiện: AI viết test luật trước khi đọc PRD-0, phải đổi nhiều test; phát hiện khi đối chiếu tài liệu.
- Nếu làm lại: chốt thứ tự merge và tên lệnh chạy (bench, soak) ngay đầu Phase 4; viết bot soak có điều khiển người chơi từ đầu.
