# TICKET-03 — Change Request "Mùa Nước Nổi" (Phase 3)

> Chép từ tab Phase 3 của lab board (phát hành 10:59). 35 phút (1:55–2:30) · Test Contract v1.2 · Hạn tag `phase-3` 2:30. [THAY THẾ] = luật đổi so với bản đang chạy.

Nước lũ về, trời nóng làm nguyên liệu mau ươn. Khách muốn biết độ tươi của từng nguyên liệu, từ lúc lấy được đến khi vào bếp.

## 1. Lõi — Độ tươi

### [THAY THẾ] Kho đếm theo loại → kho cá thể
```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```
- File có đúng khóa gốc `items`, giá trị là mảng cá thể `{id,kind,fresh}`. Kho rỗng `{"items":[]}`. `id` chuỗi duy nhất, khác rỗng; `kind` thuộc danh mục nguyên liệu; `fresh` hữu hạn trong [0,100].
- Cấp `I1, I2, …` theo thứ tự vào giỏ, tiếp tục tăng xuyên pha và Ngày, kể cả khi cá thể trước đã dùng hoặc bỏ. LIFO khi mất hàng vẫn theo thứ tự vào giỏ.
- Bên đọc chọn schema theo `contract_version`. Contract v1.2 trả **mã 2** cho file kho đếm hoặc sai schema, kind lạ, id trùng, fresh ngoài miền. Kho quán nhận nguyên số lượng, id và độ tươi, kể cả hàng ươn. Sức chứa giỏ chỉ áp lên giỏ.
- `gather --inventory-out` ghi đúng một lần khi có `gather_end`, file tạm cùng thư mục rồi thay thế nguyên tử. Ngất ghi kho rỗng. Chạm `--ticks` trước `gather_end` thì giữ nguyên đường dẫn đích. Xuất file theo id, đủ độ chính xác khi đọc lại để giữ giá trị và nhánh ở ngưỡng 30. `gather_end.data.inventory` cùng schema.
- Trong `day`: bàn giao trong cùng tick chuyển pha, hàng không hao thêm, ca quán chạy từ bước sau. Nếu có Chợ Chú Sáu, hàng mua nhập riêng vào kho quán Ngày kế với `fresh:100`, tách khỏi `gather_end.inventory`, dùng id mới. Hàng thô ở Shop hoặc chờ nhập không hao tươi. Khi người chơi bán, lấy cá thể **chưa ươn tươi nhất** của loại, hòa theo id.

### Độ tươi, giữ chỗ và giá
| Quy tắc | Cách xử lý |
|---|---|
| Hàng mới | `fresh = 100` lúc bắt/hái, bắt đầu hao từ bước sau. |
| Hao tươi | Giỏ −0.5/s, kho quán −0.25/s kể cả hàng đang giữ chỗ. 60 tick/s, kẹp đáy 0. Pause dừng hao. Món chín không hao. |
| Ươn | `fresh < 30`: vẫn chiếm ô, không dùng nấu. Phát `spoiled` đúng một lần khi đi từ ≥ 30 xuống < 30. Nhiều cá thể cùng vượt ngưỡng thì phát theo id. So ngưỡng trước làm tròn. |
| [THAY THẾ] Giữ theo lượng → giữ theo id | Mỗi loại trong công thức lấy các cá thể khả dụng tươi nhất, hòa theo id. Nếu phần giữ có cá thể vừa ươn: nhả toàn bộ phần giữ của đơn và thử giữ lại **đúng một lần**. Xử lý các đơn bị ảnh hưởng theo `order_tick` rồi id bàn. Không đủ thì đơn thường chuyển `unfulfillable`, khách chờ tới hạn. |
| [THAY THẾ] Giá niêm yết → giá theo tươi | Bắt đầu nấu: tiêu đúng các id đang giữ, chốt `base_price = floor(giá niêm yết × trung bình fresh của các cá thể dùng / 100)`. Boa `floor(tiền món × 0.2)` trên giá đã chốt. Điểm vẫn `earned + 100 × floor(reputation)`. |
| HUD | Người chơi đọc được độ tươi hoặc nhận ra hàng ươn (số, thanh, nhãn hoặc biểu tượng). |

Dùng phép tính đủ chính xác ở ngưỡng 30 và phép floor. Gợi ý: 240 đơn vị mỗi điểm tươi; gather trừ 2 đơn vị/tick, quán trừ 1 đơn vị/tick.

### Thứ tự trong tick
- **Gather:** đồng hồ, cooldown, hồi nút **và độ tươi hàng có sẵn ở đầu bước** → lịch dòng lũ nếu bật → bơi, oxy, ngạt → Lao nếu có, rồi thủy quái/hit → bến trước hái → bắt cá rồi ảnh nếu có → xét hết giờ; còn giờ mới cập nhật cá và sinh thêm. Rơi hàng theo LIFO. Ngất: bỏ toàn bộ phần còn lại theo LIFO rồi `faint`, `gather_end(fainted)`.
- **Quán:** đồng hồ và timer → hao tươi kho thô, phát hết `spoiled` theo id rồi mới xử lý giữ chỗ bị ươn → món chín/cháy theo id bếp → di chuyển và tối đa một tương tác → thanh toán, kiên nhẫn/đóng ca → còn giờ: đặt trước (nếu có) rồi khách thường. Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ. Giao đúng tick kết thúc ca được trả ngay.

### Contract v1.2
- [THAY THẾ] `contract_version: "1.2"`. Thêm `freshness {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below}` = 100, 0.5, 0.25, 30.
- **Scenario:** `gather.hold` và `quan.stock` là mảng cá thể. Trong `day`, Ngày đầu giữ nguyên id trong mẫu `gather.hold`, các Ngày kế cấp id mới theo thứ tự mảng với kind/fresh ban đầu. `customers[].reserved` là mảng id cá thể. Id vật lý duy nhất giữa các nơi chứa. Phần giữ phải trỏ tới cá thể chưa ươn trong kho, đủ công thức, không dùng chung với đơn khác. Bỏ `reserved` cho đơn reserved thì cấp theo `order_tick` rồi id bàn, lấy tươi nhất rồi id nhỏ. Sai/mâu thuẫn → mã 2. Payload món giữ cấu trúc, `base_price` là giá đã chốt theo fresh.
- **JSONL:** snapshot `hold`, `stock` (quán và Shop) và `customers[].reserved` theo schema trên. `cook_started.data.items` là mảng cá thể sắp theo kind rồi id. `lost` trong `monster_hit`/`faint` là mảng cá thể theo thứ tự bỏ LIFO. Event mới `spoiled {item_id, kind, location ("hold"/"stock")}`. Dung sai độ tươi ±0.01. Tick event biên chính xác.
- Kiểm ngưỡng (gather một bước, không input), cá thể bắt đầu đúng fresh 30 nên ươn ở bước đầu:
  ```json
  {"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}
  ```
  → `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}`
- Smoke bàn giao: cùng mẫu với `fresh:100`, `interact:true` ở frame 0 để cập bến; mở `quan --inventory` file vừa ghi, `--ticks 0`; so chính xác id, kind, độ tươi của snapshot quán với file (sau lần hao ở bước gather).

## 2. Mở rộng (nhóm 4 người không bắt buộc)
Dòng nước lũ (`current`) và Khách đặt trước (`reservations`) — chỉ làm khi lõi đã ổn; khai trong `extensions`, có test/bằng chứng. Nhóm 6667 (4 người): **không làm** ở phase này.

## 3. Quy trình nhóm / DoD
- Ghi tác động (module, file, test, người), quyết định đổi schema, thứ tự tích hợp giữ `main` chạy được.
- `CHANGELOG.md`: breaking change, schema mới, cách cập nhật fixture. Trên `main` kiểm cả file và `day`, chạy lại regression P1–P2 còn hiệu lực; ghi lý do nếu test cũ bị thay bởi luật mới.
- Bằng chứng `docs/proof/phase-3/`, ma trận `docs/verification/phase-3.md` (AC-P3-xx → bằng chứng → kết quả). Cập nhật `docs/clarify.md`, `docs/ai-usage-log.md`, retro nhanh về lần đổi kho trong `docs/retro.md`.
- DoD: (1) v1.2 bàn giao kho cá thể qua file và trong day, kho đếm → mã 2, id/độ tươi/ươn/giữ chỗ/giá/JSONL đúng; (2) HUD thấy độ tươi/hàng ươn, test qua ngưỡng, giữ lại khi vừa ươn, chốt giá, bàn giao; (3) ghi tác động + thứ tự tích hợp, đóng góp từng người; (4) CHANGELOG, regression đạt, verification + bằng chứng khớp commit gắn tag, clarify + ai-log; (5) mở rộng nếu có; (6) tag `phase-3` trên `main`.
