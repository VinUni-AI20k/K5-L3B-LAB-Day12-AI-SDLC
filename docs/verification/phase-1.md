# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Lát 1 — oxy, ngạt và ngất | `GatherSlice1Test` kiểm tick oxy vừa cạn, lên mặt đúng hạn ngạt và mất giỏ LIFO | [Kiểm tra bản bàn giao](../proof/phase-1/gather-handoff.md) | Đạt |
| Lát 2 — hái, bắt cá, giỏ và cập bến | `GatherSlice2Test` kiểm hồi nút, ưu tiên bến, đủ chỗ cả đàn và cooldown | [Kiểm tra bản bàn giao](../proof/phase-1/gather-handoff.md) | Đạt |
| Lát 4 — PRD F: tương tác sau di chuyển, đúng bán kính, ưu tiên khoảng cách/bếp/id; mỗi cạnh lên một lượt | `tests/test_quan_service.py`: radius, movement, priority, natural id, held input | [Log test](../proof/phase-1/chur04-tests.txt) | Đạt trong phạm vi lát 4 |
| Lát 4 — PRD D/E/F: đơn cũ nhất, tiêu nguyên liệu giữ, payload theo order_id, nấu/bưng/phục vụ | Test service flow, sorted items, oldest order, full hand, wrong order | [Fixture, lệnh và kết quả](../proof/phase-1/chur04-service.md) | Đạt |
| Lát 4 — PRD F: deadline kiên nhẫn, floor tip, chốt boa khi phục vụ, thu tiền khi ăn xong, kẹp uy tín | Test deadline, threshold, floor, frozen tip, reputation, single payment | [Log test](../proof/phase-1/chur04-tests.txt) | Đạt |
| Lát 4 — PRD E/F: đóng ca thu tiền khách vừa ăn, waiting rời không trừ uy tín, dọn món không hoàn nguyên liệu | Test closing, payment reason, cleanup, settlement table order | [Log test](../proof/phase-1/chur04-tests.txt) | Đạt |
| Lát 4 — PRD B/E: headless tất định và lỗi payload mã 2 trước ghi output | Hai tiến trình CLI cùng seed/input so từng byte; bảo toàn output sentinel khi fixture lỗi | [Output JSONL](../proof/phase-1/chur04-service-output.txt), [bằng chứng](../proof/phase-1/chur04-service.md) | Đạt cho các tình huống đã kiểm; chưa thay kiểm schema toàn bộ của lát 3 |
| PO — chốt câu hỏi theo PRD-0 | Đối chiếu toàn văn PRD người dùng cung cấp | [clarify #1–#8](../clarify.md) | Đã có câu trả lời từ PRD; không ghi nhận hỏi giảng viên |
| Toàn bộ luật gather, lịch sinh khách, kiểm schema scenario đầy đủ, HUD, skill nhóm và tag | Cần kiểm riêng các lát còn lại và main sau tích hợp | Xem giới hạn trong [bàn giao chur04](../proof/phase-1/chur04-service.md) | Chưa xác nhận DoD toàn Phase 1 |

## Đánh giá ngắn
- Lát 4 có 28 test riêng đạt; toàn repo 60 test đạt với launcher Python thay tạm trên Windows (chi tiết trong bằng chứng). Đây chưa là kết quả commit bàn giao/tag trên main.
- Cần tích hợp lát 3, tránh giảm timer và xử lý khách rời hai lần. Các lát khác cần tự bổ sung bằng chứng thực tế trước khi xác nhận toàn Phase 1.
