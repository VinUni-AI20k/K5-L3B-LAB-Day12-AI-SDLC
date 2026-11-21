# Kế hoạch Phase 2

Mục tiêu là hoàn thành Ticket-02 từ `phase-1` tại `ad79355`. Chạy một Ngày trọn vòng Lặn & Hái → Mở Quán → Shop, theo Test Contract v1.1 và dữ liệu chuẩn. Xem [giao diện và dữ liệu bàn giao](../contracts/phase-2.md). Phạm vi là lõi.

| AC | Việc | Người và nhánh | Bằng chứng cần có |
|---|---|---|---|
| AC-P2-01 | Cá bơi, phản xạ, đổi hướng, 8 đàn đầu ca, sinh theo lịch, hai nút kèo nèo mới. | Diên · `phoenix/p2-gather` | Test seed lặp lại, lịch 120/360 tick, giới hạn 12 đàn và `random_fish:false`. |
| AC-P2-02 | Cá Sấu Năm Chèo, hit, bất tử, recoil, rơi LIFO và ngất. | Diên · cùng nhánh | Test M2 từ Ngày 3, ngưỡng chạm, khoảng bất tử và bàn giao kho rỗng khi ngất. |
| AC-P2-03 | Quán 2 bếp, 4 bàn và 6 món, chọn món theo kế hoạch khi chạy `day`. | Nhân · `phoenix/p2-quan` | Test bàn trống nhỏ nhất, một đơn giữ hàng, nhiều bàn và quán độc lập dùng đủ menu. |
| AC-P2-04 | Runner và dữ liệu v1.1, CLI `day`, Shop, pause và nâng cấp. | Khôi · `phoenix/p2-day` | Test chuyển pha, tick pause, mua đúng giá, cấp có hiệu lực từ Ngày sau, giới hạn ngày và mã 2 khi fixture sai. |
| AC-P2-05 | Menu, giới thiệu hai ca, kết quả, Shop, tổng kết và HUD. | Khôi · cùng nhánh | Chạy một Ngày trên trình duyệt, kiểm cảnh báo, tiến độ bếp, pause và chỉ số đọc được ở 1280×720. |
| AC-P2-06 | Smoke hai tiến trình, `day` và hồi quy, bằng chứng, retro, tag. | Khôi · tích hợp cùng Diên và Nhân | Lưu `docs/proof/phase-2/integration.*`, kiểm headless một Ngày trong 20 giây và điền `docs/verification/phase-2.md`. |

## Trình tự và bàn giao

1. Diên và Nhân có thể tách nhánh từ tag `phase-1` và bắt đầu ngay khi nhận tài liệu cùng dữ liệu chuẩn. Mỗi người sở hữu file sim và test riêng, có thể nạp delta tuning trong fixture để test lát mình. Khôi review giao diện và phụ trách manifest, adapter, runner và HUD. Khi cần sửa file dùng chung, báo Khôi để thống nhất trước khi tích hợp.
2. Diên tách cá bơi/sinh và cá sấu thành các commit có nội dung. Nhân tách nhiều bếp/bàn với menu mở rộng và lọc kế hoạch thành hai commit có nội dung, kèm test. Khôi dựng luồng ngày bằng fixture cố định song song. Hai lát có thể push và mở PR sớm, chỉ chờ ở bước cần adapter hoặc phải bật v1.1 cùng nhau.
3. Rà tiến độ và chạy smoke kho ở mốc 20 phút của đợt build. Gather và Quán vào `main` trước, giữ v1.0. Khôi nối phần vòng ngày trên nền hai PR đã gộp, bật v1.1 và kiểm toàn luồng trong PR cuối.
4. Kiểm nhiều Ngày, nâng cấp và P1 còn hiệu lực. Khôi review bằng chứng, cập nhật AI log và retro có một hành động cho Phase 3, rồi gắn `phase-2` đúng commit bàn giao.
