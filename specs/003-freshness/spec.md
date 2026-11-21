# Feature Specification: Phase 3 — Mùa Nước Nổi: kho cá thể + độ tươi (Test Contract v1.2)

**Feature Branch**: không tạo (làm trên `tv6/phase-1-team-ai`); thư mục `specs/003-freshness/`
**Created**: 2026-11-21 · **Status**: Draft (đã clarify theo đề; đề im lặng → `GIẢ ĐỊNH`)
**Input**: TICKET-03 — `docs/prd/phase-3-ticket-03.md`; chia việc theo `.lab-notes/brief-phase-2-3.html` mục "Chia việc Phase 3".
**Phụ thuộc**: `specs/001-phase-1-core` (lõi), `specs/002-day-loop` (v1.1, `day`). **Hiện trạng code (đo 2026-11-21)**: contract còn v1.0; hái/bắt cá còn TODO; `quan.py` mới có hàm rời (`start_cooking`, `serve_dish`…) chưa nối vào `step`; `--mode day` chưa chạy. 32 test OK (chỉ phủ khung). → P3 xây trên nền P1/P2 chưa xong: các AC về quán/day chỉ kiểm được khi P1/P2 xong.

> [THAY THẾ] = luật đổi so với v1.1. Số liệu từ `game.contract.json` v1.2: `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Adapter: kho cá thể v1.2 (Priority: P1, làm trước)
[THAY THẾ] Kho đếm → kho cá thể `{"items":[{"id","kind","fresh"}]}`. Bên đọc chọn schema theo `contract_version`; v1.2 từ chối kho đếm.
**Independent Test**: `quan --inventory <file> --ticks 0` với file đúng/sai; `gather --inventory-out`.
**Acceptance**:
1. File đúng `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}` → mã 0, snapshot `stock` đúng id/kind/fresh; kho rỗng `{"items":[]}` hợp lệ.
2. Kho đếm `{"items":{"ca_loc":1}}`, khóa gốc lạ, id trùng/rỗng, kind lạ, fresh ngoài [0,100] hoặc không hữu hạn → mã 2, không ghi đầu ra.
3. Kho quán nhận đủ số lượng, id, độ tươi, kể cả hàng ươn (không giới hạn sức chứa).
4. `--inventory-out` ghi đúng một lần khi `gather_end`, qua file tạm cùng thư mục rồi thay thế nguyên tử; ngất → `{"items":[]}`; chạm `--ticks` trước → đường dẫn đích giữ nguyên. Xuất sắp theo id, đủ chính xác khi đọc lại giữ đúng giá trị/nhánh ở ngưỡng 30. `gather_end.data.inventory` cùng schema.

### User Story 2 — Lặn: cá thể trong giỏ, hao tươi, ươn (P1)
**Independent Test**: `gather` với scenario `hold` cá thể.
**Acceptance**:
1. Hái/bắt → mỗi món một cá thể `fresh:100`, id `I1, I2…` theo thứ tự vào giỏ, tăng xuyên pha và Ngày (không tái dùng id đã dùng/bỏ).
2. Hàng mới hao từ bước sau; giỏ −0.5/s (−0.5/60 mỗi tick), kẹp 0; pause không hao.
3. `spoiled {item_id, kind, location:"hold"}` đúng một lần khi đi từ ≥ 30 xuống < 30 (so trước làm tròn); nhiều cá thể cùng bước → theo id. Hàng ươn vẫn chiếm ô.
4. Scenario đề `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}`, 1 bước không input → event `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}`.
5. Rơi hàng (`monster_hit`) và ngất bỏ theo LIFO cá thể; `lost` là mảng cá thể theo thứ tự bỏ; ngất bỏ toàn bộ rồi `faint`, `gather_end(fainted)`.

### User Story 3 — Quán: hao tươi, giữ chỗ theo id, giá theo tươi (P1)
**Independent Test**: `quan` với `quan.stock` cá thể + `customers[].reserved` mảng id.
**Acceptance**:
1. Kho quán −0.25/s, kể cả hàng đang giữ chỗ; món chín không hao; pause không hao. `spoiled {location:"stock"}` theo id.
2. [THAY THẾ] Giữ chỗ theo id: mỗi loại trong công thức lấy cá thể khả dụng (chưa ươn, chưa bị giữ) tươi nhất, hòa theo id; `customers[].reserved` là mảng id.
3. Phần giữ có cá thể vừa ươn → nhả toàn bộ phần giữ của đơn, thử giữ lại đúng một lần; các đơn bị ảnh hưởng xử lý theo `order_tick` rồi id bàn; thiếu → `unfulfillable`, khách chờ tới hạn.
4. [THAY THẾ] Bắt đầu nấu tiêu đúng các id đang giữ, chốt `base_price = floor(giá niêm yết × fresh TB / 100)`; boa `floor(base_price × 0.2)` nếu đủ điều kiện; điểm giữ `earned + 100 × floor(reputation)`.
5. `cook_started.data.items` = mảng cá thể sắp theo kind rồi id.
6. Thứ tự tick quán: đồng hồ/timer → hao tươi kho, phát hết `spoiled` theo id → xử lý giữ chỗ bị ươn → món chín/cháy theo id bếp → di chuyển + tối đa một tương tác → thanh toán, kiên nhẫn/đóng ca → (còn giờ) đặt trước nếu có → khách thường. Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ; giao đúng tick hết ca được trả ngay.

### User Story 4 — Bàn giao trong `day` (P1)
**Acceptance**:
1. Bàn giao kho trong cùng tick chuyển pha `gather → quan`, không hao thêm; ca quán chạy từ bước sau.
2. Id tăng xuyên Ngày; Ngày đầu giữ id trong mẫu `gather.hold`, Ngày kế cấp id mới theo thứ tự mảng với kind/fresh ban đầu.
3. Hàng ở Shop (stock dư) không hao tươi.

### User Story 5 — HUD độ tươi (P2 — Cursor)
Người chơi đọc được độ tươi hoặc nhận ra hàng ươn (số, thanh, nhãn hoặc biểu tượng) ở giỏ và kho quán. `tests/test_live.py` giữ xanh.

### Edge Cases
- `fresh` đúng 30 → chưa ươn; xuống 29.99… ở bước sau → `spoiled`.
- Cá thể bắt đầu < 30 trong scenario → không phát `spoiled` (không đi qua ngưỡng).
- Kẹp đáy 0: không âm, không phát lại `spoiled`.
- Nhiều cá thể cùng ươn một bước → nhiều `spoiled` theo id, trước khi xử lý giữ chỗ.
- Hai đơn cùng mất phần giữ một bước → thử giữ lại theo `order_tick` rồi id bàn; đơn trước được ưu tiên.
- Kho có hàng ươn: không dùng để nấu, không được khách tính là "nấu được".
- Smoke file: sau bước gather (cập bến ở frame 0) fresh đã hao 1 tick → `100 − 0.5/60`; quán `--ticks 0` phải đọc lại chính xác giá trị đó (±0.01).

## Requirements *(mandatory)*
- **FR-301** (Adapter): Schema kho cá thể; đọc theo `contract_version`; v1.2 → kho đếm/sai schema mã 2. `KINDS` theo danh mục nguyên liệu v1.1 (6 loại).
- **FR-302**: Ghi kho nguyên tử, một lần, sắp theo id, đủ chính xác (GIẢ ĐỊNH: số thực JSON đầy đủ, không làm tròn 3 chữ số như JSONL).
- **FR-303** (Lặn): Cá thể `I<n>`; bộ cấp id toàn cục cho cả lượt chạy (xuyên pha/Ngày); hao giỏ 0.5/s từ bước sau khi lấy; `spoiled` ngưỡng 30, theo id; LIFO cá thể khi rơi/ngất.
- **FR-304** (Quán): Hao kho 0.25/s; giữ chỗ theo id (tươi nhất, hòa id); thử giữ lại 1 lần khi phần giữ vừa ươn; `unfulfillable`.
- **FR-305** (Quán): `base_price` chốt khi bắt đầu nấu; boa trên giá chốt; `cook_started.items`.
- **FR-306** (day): Bàn giao cùng tick không hao thêm; id xuyên Ngày; Shop không hao; pause không hao.
- **FR-307** (Scenario): `gather.hold`, `quan.stock` mảng cá thể; `customers[].reserved` mảng id; id vật lý duy nhất giữa mọi nơi chứa; reserved phải trỏ cá thể chưa ươn trong kho, đủ công thức, không dùng chung; đơn `reserved` thiếu `reserved` → cấp theo `order_tick` rồi id bàn (tươi nhất, id nhỏ); sai → mã 2.
- **FR-308** (JSONL): snapshot `hold`, `stock` (quán, Shop), `customers[].reserved` theo schema mới; event `spoiled {item_id,kind,location}`; dung sai fresh ±0.01; tick event biên chính xác.
- **FR-309**: Tính toán chính xác ở ngưỡng: đơn vị nguyên **240 đơn vị/điểm tươi** (gather −2/tick, quán −1/tick); `fresh` xuất = đơn vị/240.
- **FR-310** (Contract): `contract_version:"1.2"`, khóa `freshness`; chỉ bật v1.2 khi hai đầu bàn giao sẵn sàng.

### Acceptance Criteria (headless JSONL)
| AC | Nội dung | FR | Cách kiểm |
|---|---|---|---|
| AC-P3-01 | Contract v1.2 nạp được, có `freshness` đúng 4 giá trị | FR-310 | `quan --ticks 0` mã 0; unit đọc contract |
| AC-P3-02 | Kho cá thể hợp lệ (gồm `{"items":[]}`, hàng ươn) đọc đúng vào `stock` | FR-301 | `quan --inventory --ticks 0` |
| AC-P3-03 | Kho đếm v1.0 → mã 2, không tạo `--out` | FR-301 | `{"items":{"ca_loc":1}}` |
| AC-P3-04 | Id trùng/rỗng, kind lạ, fresh < 0 / > 100 / NaN, khóa gốc lạ → mã 2 | FR-301 | 5 file lỗi |
| AC-P3-05 | `--inventory-out` ghi một lần, nguyên tử (không còn file tạm), sắp theo id; ngất → `{"items":[]}`; `tick_limit` → đích giữ nguyên | FR-302 | 3 kịch bản gather |
| AC-P3-06 | Hái/bắt cấp `I1, I2…` theo thứ tự vào giỏ, `fresh:100`, hao từ bước sau | FR-303 | gather fixture |
| AC-P3-07 | Giỏ hao 0.5/s: sau 60 tick fresh = 99.5 (±0.01) | FR-303/309 | hold fresh 100, `--ticks 60` |
| AC-P3-08 | Scenario mẫu của đề → `spoiled` I1 ở tick 1, location `hold`, đúng 1 lần | FR-303 | `--ticks 1` rồi `--ticks 600` |
| AC-P3-09 | Nhiều cá thể cùng vượt ngưỡng → `spoiled` theo id | FR-303 | hold I2, I1 cùng fresh 30 |
| AC-P3-10 | `monster_hit.lost` / `faint.lost` là mảng cá thể theo LIFO | FR-303 | hold 5 cá thể + Cá Sấu |
| AC-P3-11 | Kho quán hao 0.25/s kể cả hàng giữ; `spoiled` location `stock` | FR-304 | quan stock fresh 30.0 |
| AC-P3-12 | Giữ chỗ lấy cá thể tươi nhất, hòa id; `customers[].reserved` mảng id | FR-304 | stock 2 cá thể khác fresh |
| AC-P3-13 | Phần giữ vừa ươn → nhả, thử giữ lại 1 lần (thành công → reserved id mới) | FR-304 | khách reserved I1 fresh 30 + I2 fresh 80 dư |
| AC-P3-14 | Thử giữ lại thất bại → `unfulfillable`, khách chờ tới hết kiên nhẫn | FR-304 | không có cá thể dư |
| AC-P3-15 | `cook_started.data.items` mảng cá thể sắp kind rồi id; tiêu đúng id đang giữ | FR-305 | quan cook |
| AC-P3-16 | `base_price = floor(giá × fresh TB / 100)`; boa `floor(base_price×0.2)`; `paid` khớp | FR-305 | ca_loc fresh 50 → base 30, tip 6 |
| AC-P3-17 | Scenario v1.2 sai (reserved trỏ hàng ươn/không tồn tại/dùng chung, id trùng giữa nơi chứa) → mã 2 | FR-307 | quan scenario |
| AC-P3-18 | Smoke bàn giao file của đề: gather (fresh 100, interact frame 0) → `quan --inventory --ticks 0` khớp id/kind/fresh | FR-301/302 | lưu `docs/proof/phase-3/` |
| AC-P3-19 | `day`: bàn giao cùng tick, không hao thêm; snapshot quán đầu = `gather_end.inventory` | FR-306 | day --days 1 |
| AC-P3-20 | `day` nhiều Ngày: id tăng xuyên Ngày; Ngày kế cấp id mới cho mẫu `gather.hold` | FR-306 | day --days 2 |
| AC-P3-21 | Pause không hao; Shop không hao | FR-306 | day + pause |
| AC-P3-22 | Regression P1–P2 còn hiệu lực xanh; test đổi do luật mới có lý do (CHANGELOG) | — | toàn bộ test |
| AC-P3-23 | Tất định: chạy 2 lần giống từng byte (gather, quan, day) | FR-309 | `cmp` |

### Key Entities
- **Item** (cá thể): `id` (`I<n>`), `kind`, `fresh` [0,100] (nội bộ: số nguyên đơn vị/240), `spoiled` suy ra (`fresh < 30`).
- **Hold**: mảng Item theo thứ tự vào giỏ (LIFO), ≤ 12.
- **Stock** (quán/Shop): mảng Item, không giới hạn.
- **Order/Customer**: `reserved` mảng id, `order_tick`, trạng thái đơn (`reserved`, `unfulfillable`, đang nấu…), `base_price` chốt khi nấu.
- **ItemIdAllocator**: bộ đếm `I<n>` toàn cục cho cả lượt chạy.

## Success Criteria *(mandatory)*
- **SC-301**: AC-P3-01…23 có test/scenario; xanh trước tag `phase-3` (2:30), phần chưa đạt ghi trung thực ở `docs/verification/phase-3.md`.
- **SC-302**: Smoke bàn giao file (AC-P3-18) đạt ở phút 20 trên bản tích hợp.
- **SC-303**: Regression P1–P2 còn hiệu lực 100% xanh; CHANGELOG ghi breaking change + cách cập nhật fixture.

## Clarifications
### Session 2026-11-21 (theo đề; im lặng → GIẢ ĐỊNH)
- Q: Đơn vị chính xác? → A: theo gợi ý đề: 240 đơn vị/điểm, gather −2/tick, quán −1/tick (0.5/s, 0.25/s).
- Q: Kho file làm tròn? → A: GIẢ ĐỊNH: ghi `fresh` = đơn vị/240 dạng số thực Python đầy đủ (không round 3), đọc lại nhân 240 và làm tròn về nguyên gần nhất.
- Q: Snapshot/JSONL làm tròn fresh? → A: JSONL vẫn làm tròn 3 chữ số (khung `jsonl.py`), dung sai ±0.01 theo đề.
- Q: Prefix id hàng do bên nào cấp khi scenario/kho nạp có id khác dạng (vd. "X7")? → A: GIẢ ĐỊNH: giữ nguyên id nạp; bộ cấp tiếp tục từ `max(n của id dạng I<n>) + 1`.
- Q: Kho quán độc lập (`quan --inventory`) cấp id gì nếu cần? → A: không cần cấp (quán không sinh hàng ở lõi).
- Q: `unfulfillable` có hiển thị ở snapshot? → A: GIẢ ĐỊNH: `customers[].order_status:"unfulfillable"` (tên trường chốt ở `docs/contracts/` bởi TV1).
- Q: Khách thường chọn món "nấu được" có tính hàng ươn? → A: không (ươn không dùng nấu).
- Q: v1.1 còn đọc kho đếm? → A: có — bên đọc chọn schema theo `contract_version`; chỉ v1.2 từ chối.
- Q: Hàng thô ở Shop hiển thị? → A: `stock` của Shop theo schema cá thể, không hao.

## Assumptions
- Phải sửa file khung `inventory.py`, `contract.py` (TV1), `scenario.py`, `headless.py`, `runner.py` (agent khung TV6) — theo bảng tác động brief.
- Mở rộng P3 (`current`, `reservations`): **tùy chọn, sau lõi**; không có AC ở spec này. Dự phòng Phase 4.
