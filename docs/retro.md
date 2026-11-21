# Retro nhóm

## Phase 1

- Mẫu kho cho phép Gather và Quán chạy kiểm chứng riêng. Bản tích hợp qua smoke hai tiến trình và chạy lặp lại phiên phục vụ với output giống từng byte.
- Review HUD phát hiện snapshot thiếu bộ đếm có thể tạo nhãn `NaN:NaN`. Đã sửa và kiểm lại với cả trường hợp thiếu giá trị và giá trị số.
- Việc mang sang Phase 2. Khôi chốt tuning và giao diện chuyển pha trước khi gộp phần dùng chung. Diên và Nhân giữ fixture riêng để kiểm hai ca trước smoke tích hợp.

## Phase 2 (nhanh)
- Hợp đồng kho đếm và giao diện chuyển pha giúp Gather, Quán và Session phát triển riêng. Khi ghép, file kho và snapshot Quán tick 0 khớp, kể cả hai nguyên liệu mới.
- Bật v1.1 làm lộ ba giả định test cũ về số đàn cá, chế độ `day` và nút `attack`. Nhóm cần đối chiếu những kỳ vọng phụ thuộc version với Ticket-02 khi đổi manifest.
- Phase 3, Khôi chuẩn bị cặp fixture kho v1.1/v1.2 trước khi sửa adapter. Diên và Nhân dùng cùng fixture để kiểm bàn giao từ Gather sang Quán. Khôi kiểm cả lỗi nhận schema cũ và smoke kho mới trước khi gắn tag.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
