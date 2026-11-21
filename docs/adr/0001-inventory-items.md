# ADR 0001 về kho cá thể

**Trạng thái triển khai.** Bản tích hợp đã áp dụng schema và chạy kiểm chứng. Khôi review trước khi merge. Bản gốc là `phase-2` tại `5455042`. Quyết định phục vụ Ticket-03 và thực hiện hành động về fixture đổi schema trong retro Phase 2.

## Bối cảnh và quyết định

Kho đếm theo loại của v1.1 ghi đủ số lượng nhưng không theo dõi được cá thể, độ tươi và nguyên liệu đang giữ cho từng đơn. v1.2 dùng một bản ghi cho mỗi cá thể. Đổi cả hai đầu và bật manifest trong cùng thời điểm sẽ yêu cầu cả nhóm tích hợp trên một nhánh. Nhóm chọn giữ đường chạy v1.1 qua hai PR đầu để mỗi lát có thể review và test riêng.

PR #7 của Diên đưa adapter lên `main` trước. PR #8 của Nhân nối Quán. Trong PR cuối, Khôi nối adapter vào Gather và các điểm bàn giao, bật v1.2 rồi kiểm hai đầu. CLI v1.2 chọn schema theo version và trả mã 2 cho file kho đếm. Tag P1/P2 tiếp tục lưu các bản chạy schema cũ.

Độ tươi nội bộ dùng phân số chính xác để phép trừ mỗi tick, so ngưỡng 30 và floor giá diễn ra trước khi chuyển sang số JSON. Dùng cùng helper cho file và snapshot, chia sẻ bản sao kho cá thể nội bộ qua `day`. Chi tiết giao diện và thứ tự tick nằm trong [hợp đồng v1.2](../contracts/phase-3.md).

## Bảng tác động

| Module | Tệp chính | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter | `chonoi/inventory.py`, `chonoi/freshness.py` | Đọc/ghi mẫu v1.1 và v1.2, từ chối ID hoặc schema sai, ghi nguyên tử, precision sau vòng file. | Diên |
| Gather | `chonoi/sim/gather.py` | Hái/bắt cấp ID, giỏ, hao tươi, ngưỡng 30, LIFO và `gather_end`. | Diên |
| Quán | `chonoi/sim/quan.py` | Giữ theo ID, cấp lại, loại hàng ươn, giá và boa. Giữ test giao sát hạn, đóng ca và lọc kế hoạch. | Nhân |
| CLI, scenario và JSONL | `chonoi/headless.py`, `chonoi/live.py`, `chonoi/scenario.py`, `chonoi/runner.py`, `chonoi/jsonl.py`, manifest | Đọc đúng version, lỗi mã 2, không làm tròn sai độ tươi, smoke file. | Khôi |
| Day, Shop và HUD | `chonoi/day.py`, `chonoi/web/index.html` | Bàn giao ngay tick chuyển, ID xuyên Ngày, pause/Shop giữ fresh, kho khả dụng từ cá thể và nhãn ươn. | Khôi |

Các kỳ vọng test phụ thuộc vào map đếm, chuỗi trong giỏ và giá niêm yết được sửa kèm lý do. Giữ các test P1–P2 còn hiệu lực như chuyển động, lượng nguyên liệu, pause, nâng cấp, thứ tự chuyển pha và thanh toán. Lưu fixture, lệnh và kết quả thực tế trong bằng chứng Phase 3 trước khi gắn tag.
