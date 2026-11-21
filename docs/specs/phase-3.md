# Spec — Phase 3: Mùa Nước Nổi (contract v1.2)

> Nguồn: TICKET-03 / PRD Phase 3 (lab board `#phase-3`). Đây là **change request**: đổi schema kho,
> không phải thêm tính năng. Quyết định kiến trúc: `docs/adr/0001-kho-ca-the-va-do-tuoi.md`.

## Problem Statement

Kho hiện đếm theo loại (`{"ca_linh": 3}`): mọi con cá linh giống hệt nhau, không có khái niệm tươi/ươn,
và giá món là hằng số. Người chơi không có lý do quay về sớm, không có lý do bỏ hàng, và buổi tối không có
quyết định nào ngoài "nấu đúng món". Mùa nước nổi đòi hỏi hàng mang về phải **có tuổi**: bắt lâu thì ươn,
ướn thì không nấu được, và giá bán phản ánh độ tươi.

## Solution

Kho chuyển sang **cá thể**: mỗi món là `{id, kind, fresh}`. Hàng mới `fresh = 100`, hao 0.5 điểm/s trong giỏ
và 0.25 điểm/s trong kho quán. Dưới 30 là **ươn**: vẫn chiếm ô, không dùng nấu, phát `spoiled` đúng một lần.
Giữ chỗ cho khách chuyển từ "giữ theo lượng" sang "giữ theo id" (lấy cá thể tươi nhất). Giá món chốt theo
độ tươi trung bình của nguyên liệu thực dùng. Id cá thể tăng xuyên pha và xuyên Ngày.

## User Stories

1. Là người chơi, tôi muốn thấy từng con cá với độ tươi riêng, để biết con nào sắp bỏ.
2. Là người chơi, tôi muốn hàng trong giỏ hao nhanh hơn hàng trong kho, để việc về sớm có giá trị.
3. Là người chơi, tôi muốn cá ươn vẫn chiếm ô, để giỏ bị chật vì quyết định của mình.
4. Là người chơi, tôi muốn được báo khi một con vừa ươn, để không nấu nhầm.
5. Là người chơi, tôi muốn khách giữ đúng con cá tươi nhất, để món ngon không bị dùng cho đơn khác.
6. Là người chơi, tôi muốn nếu con đang giữ bị ươn thì đơn được giữ lại một lần, để không mất đơn oan.
7. Là người chơi, tôi muốn giá món cao hơn khi nguyên liệu tươi, để chăm chút có thưởng.
8. Là người chơi, tôi muốn bị cắn thì mất hàng theo LIFO, để con mới bắt là con dễ mất.
9. Là người chơi, tôi muốn độ tươi dừng hao khi tạm dừng, để pause không phạt mình.
10. Là người chơi, tôi muốn hàng mua ở Chợ nhập với độ tươi 100, để tiền mua được hàng mới.
11. Là người chơi, tôi muốn id cá thể liên tục qua các Ngày, để không bao giờ trùng id.
12. Là người chấm, tôi muốn cùng seed cho cùng byte, kể cả khi fresh là số lẻ.
13. Là người chấm, tôi muốn fixture đặt đúng `fresh = 30` để kiểm nhánh ươn ở tick 1.
14. Là người chấm, tôi muốn file kho đếm cũ bị từ chối mã 2 ở v1.2, để không lẫn schema.
15. Là người chơi, tôi muốn HUD đọc được độ tươi hoặc nhận ra hàng ươn, để không phải đoán.

## Implementation Decisions

- **Số nguyên đơn vị, không float**: 1 điểm tươi = 240 đơn vị. `fresh` lưu là `units ∈ [0, 24000]`;
  hao 2 đơn vị/tick trong giỏ, 1 đơn vị/tick trong kho; ngưỡng ươn 30 = **7200 đơn vị**. So ngưỡng trên
  số nguyên, chỉ đổi sang điểm khi xuất JSONL (`units / 240`). Lý do: PRD yêu cầu chính xác ở ngưỡng 30 và
  phép `floor`; float sẽ lệch ở biên.
- **Adapter hai schema** trong lớp kho: đọc/ghi theo `contract_version` (1.0/1.1 = đếm, 1.2 = cá thể).
  Không có nhánh `if` rải rác trong sim — chỉ một chỗ quyết định.
- **Id cá thể** cấp bằng `IdAllocator` với tiền tố `I`, tăng xuyên pha và xuyên Ngày, kể cả khi cá thể đã dùng.
- **Hao tươi** tính ở đầu bước cho hàng **có sẵn**; hàng mới nhận `fresh = 100` và bắt đầu hao từ bước sau.
  Món đã nấu chín không hao. Pause đóng băng mọi timer, kể cả hao tươi.
- **Ươn**: giữ nguyên ô, không dùng nấu; `spoiled` phát đúng một lần khi đi từ ≥ 30 xuống < 30, theo id.
- **Giữ chỗ theo id**: mỗi dòng công thức lấy cá thể tươi nhất khả dụng, hòa theo id. Nếu một cá thể đang giữ
  vừa ươn: nhả **toàn bộ** phần giữ của đơn và thử giữ lại **đúng một lần**; xử lý các đơn bị ảnh hưởng theo
  `order_tick` rồi id bàn. Không đủ thì đơn chuyển `unfulfillable`.
- **Giá theo tươi**: khi bắt đầu nấu, tiêu đúng các id đang giữ và chốt
  `base_price = floor(giá_niêm_yết × trung_bình_fresh_của_cá_thể_dùng / 100)`; boa tính trên giá đã chốt.
- **Thứ tự tick** đổi: gather thêm bước hao tươi **trước** khi bơi; quán thêm bước hao tươi kho thô + phát
  `spoiled` **trước** xử lý giữ chỗ bị ươn, rồi mới tới bếp.
- **`lost`** trong `monster_hit`/`faint` là mảng cá thể theo thứ tự bỏ LIFO (không còn là mảng kind).
- **`cook_started.items`** sắp theo `(kind, id)`.

## Testing Decisions

- Test hộp đen qua `headless_cmd`; không import module nội bộ để kiểm luật.
- Bộ test migration là bắt buộc: cùng một fixture, v1.1 phải đọc/ghi được schema đếm, v1.2 phải **từ chối**
  schema đếm bằng mã 2 và ngược lại.
- Ca biên: `fresh` đúng 30 ở tick 0 → `spoiled` ở tick 1; nhiều cá thể vượt ngưỡng cùng tick → phát theo id;
  giữ chỗ có cá thể vừa ươn → nhả và giữ lại một lần; đơn không đủ sau khi thử lại → `unfulfillable`;
  giá chốt với trung bình lẻ (làm tròn xuống); LIFO khi mất hàng; pause giữa lúc hao.
- Dung sai độ tươi ±0.01; các ngưỡng/`floor`/id/tick event biên so chính xác.
- Regression P1–P2 phải chạy lại; test cũ bị thay vì luật mới phải ghi lý do trong commit.

## Out of Scope

- Mở rộng không chọn: `current` (dòng nước lũ), `reservations` (khách đặt trước), Chợ Chú Sáu, Lao, Vợt, Rắn, Cháy.
- Phase 2 (v1.1 `day`) — P3 giả định P2 đã xong; nếu chưa, ticket 04 lùi lại.
- Đổi công nghệ, asset ngoài, lưu game.

## Further Notes

- Đây là **breaking change**: mọi fixture trong `tests/` dùng schema đếm đều phải đổi hoặc được adapter dịch.
- `CHANGELOG.md` phải ghi breaking change + cách cập nhật fixture (PRD yêu cầu).
- Bảng tác động module → file → test → người nằm trong ADR `0001`, cập nhật lại khi có file thật khác.
