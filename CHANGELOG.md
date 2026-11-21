# Changelog
## Unreleased

### Phase 4 — asset tự tạo (đồ họa SVG + SFX có phụ đề)
- 21 SVG trong `chonoi/web/assets/` sinh bởi `tools/gen_assets.py`; HUD dùng sprite cho Út Sen, cá, Cá Sấu (trước đây HUD chưa vẽ thủy quái), cây nổi, bến, bếp, bàn, khách và món; tự về hình khối cũ nếu asset chưa tải.
- 24 SFX tổng hợp bằng Web Audio (`assets/sfx.js`) kèm phụ đề; phím M tắt/bật tiếng, V ẩn/hiện phụ đề.
- `chonoi/live.py`: thêm route tĩnh `GET /assets/<tên>` (chỉ `.svg`/`.js`, tên phẳng, chặn `..` và `/`); các route `/`, `/state`, `/input`, `/restart` không đổi. Đây là file khung giảng viên nên ghi lại lý do: cần để client nạp được asset.
- `tests/test_assets.py` (12 test). Không đổi luật, tick, sự kiện, JSONL hay `game.contract.json`.
- HUD quán chừa thêm chỗ phía trên cho 3 dòng kho (trước đó bị mép phòng che).

### Phase 4 — cảnh báo và chế độ tương phản cao (AC-P4-04, AC-P4-05)
- 3 cảnh báo có **chữ + biểu tượng** (`warn_*`): "Thủy quái!" (Cá Sấu trong 1,5 × bán kính phát hiện, hoặc đang đuổi; thêm viền tím), "Oxy sắp hết!" / "Hết hơi!" (oxy < 25% / cạn, chỉ khi ở dưới nước), "Khách sắp giận!" (kiên nhẫn < 25%, kèm biểu tượng ngay cạnh khách).
- **Chế độ tương phản cao** (phím **H**, nhớ lựa chọn): chữ đậm có viền (chữ tối viền trắng, chữ sáng viền đen), viền khung dày hơn, cảnh báo nền đen, tăng tương phản và bão hòa cảnh.
- `tests/test_warnings.py` (9 test, chạy HUD thật trong Node với canvas giả; skip nếu không có Node) và bằng chứng ảnh ở `docs/proof/phase-4/`. Không đổi luật, tick, sự kiện hay JSONL.

### Phase 3 — v1.2 đã bật trên `main` (`contract_version: "1.2"`)
- Kho cá thể dùng chung `chonoi/items.py`, file kho / scenario / giỏ cá thể, giữ chỗ theo id, hao kho quán, giá theo tươi (lát 0, 3, 4). Code vẫn nhận manifest v1.1 (không có `tuning.freshness`).
- Test hộp đen Phase 3 `tests/test_fresh_p3.py` (28 test) và ma trận `docs/verification/phase-3.md`.
- HUD (`chonoi/web/index.html`) đọc được cả kho đếm (v1.1) lẫn kho cá thể (v1.2): thanh độ tươi, gạch chéo và cảnh báo hàng ươn, kho khả dụng bỏ phần giữ chỗ và hàng ươn.

### Phase 3 — `day` bàn giao kho cá thể (lát 5)
- `day`: chuyển **nguyên mảng cá thể** (id, kind, fresh) từ gather sang quán trong cùng tick, không hao thêm.
- Ngày kế: id mẫu `gather.hold` được cấp **mới** theo thứ tự mảng (kind/fresh ban đầu); id tăng tiếp xuyên pha và Ngày (clarify #19).
- Shop: giữ kho cá thể theo id, hàng thô không hao tươi; kho dư bị bỏ khi Shop đóng.
- `tests/test_day_p2.py` sửa để đúng ở cả v1.1 và v1.2 (fixture qua `mk_hold` / `mk_stock` / `stock_counts` trong `tests/qa_helpers.py`).

### Phase 3 — gather: hao giỏ và `spoiled` (lát 2)
- `GatherSim._tick_hold_freshness`: giỏ giảm 0.5/s ở đầu bước (sau hồi nút), hàng mới hao từ bước sau; `spoiled {item_id, kind, location: "hold"}` đúng một lần, theo id. Ví dụ ngưỡng `fresh: 30` của ticket phát `spoiled` ở tick 1.
- `test_lat0_v12`: hàng rơi khi bị cắn/ngất đã hao từ đầu bước (đổi vì luật mới).

### v1.2 — Ticket-03 "Mùa Nước Nổi" (hợp đồng)
**BREAKING — kho đếm theo loại → kho cá thể.** `contract_version` đổi `"1.1"` → `"1.2"`, thêm `tuning.freshness`
`{initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

| Chỗ | Trước (v1.1) | Sau (v1.2) |
|---|---|---|
| File kho `--inventory` / `--inventory-out` | `{"items": {"ca_loc": 1}}` | `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`; kho rỗng `{"items": []}`; file kho đếm cũ → mã 2 |
| `gather.hold`, `quan.stock` (scenario) | mảng kind / map kind → số | mảng cá thể `{id, kind, fresh}` |
| `customers[].reserved` | map kind → số | mảng id cá thể |
| Giỏ, kho quán trong snapshot | mảng kind / map | mảng cá thể |
| `cook_started.data.items`, `lost` (monster_hit, faint), `gather_end.data.inventory` | mảng kind / map | mảng cá thể |
| Giá món | giá niêm yết | `floor(giá niêm yết × TB fresh các cá thể dùng / 100)`, boa tính trên giá đã chốt |
| Giữ chỗ | theo lượng | theo id: cá thể tươi nhất, hòa id nhỏ; vừa ươn thì nhả hết và thử giữ lại một lần |
| Sự kiện mới | — | `spoiled {item_id, kind, location}` |

**Cách cập nhật fixture:** đổi `"hold": ["ca_loc"]` thành `"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`; `"stock": {"ca_loc": 1}`
thành mảng cá thể; `"reserved": {"ca_loc": 1}` thành `"reserved": ["I1"]`; file kho cũ phải sinh lại bằng gather v1.2.
Test cũ bị thay bởi luật mới sẽ liệt kê (kèm lý do) ở `docs/verification/phase-3.md` mục AC-P3-19.

**Bật v1.2 (trongnghia2304):**
- `game.contract.json`: `contract_version: "1.2"`, thêm `tuning.freshness`. Bộ chấm và CI đọc thẳng file này, không cần `CHONOI_CONTRACT`.
- **Test cũ dùng fixture kho đếm** chạy trên manifest v1.1 tạm qua `tests/legacy_v11.py` (Ticket-03 mục 3: "hỗ trợ hai phiên bản nội bộ trong lúc chuyển"); code vẫn nhận v1.1. Lúc gắn tag `phase-3` ghim 12 module; **sau tag** s0ra1n0 đã chuyển 5 module của mình sang kho cá thể
  (`test_smoke_p1`, `test_gather_lat1`, `test_gather_lat1_p2`, `test_lat0_v11`, `test_python_starter_units`: fixture `mk_hold`,
  kỳ vọng `lost` / `gather_end.inventory` / file kho là mảng cá thể đã hao đúng số bước, file kho đếm cũ -> mã 2).
  Còn ghim (7): `test_gather_p1`, `test_lat2`, `test_p2_lat2_fish`, `test_quan_p1`, `test_quan_lat3`, `test_quan_lat4`, `test_quan_p2`.
  Lý do: luật các test này bảo vệ (bơi, oxy, Cá Sấu, cá bơi, khách, bếp) không đổi ở v1.2; chỉ dạng kho đổi.
  Chủ mỗi file chuyển fixture sang kho cá thể (có thể dùng `mk_hold` / `mk_stock` như `test_day_p2`) rồi bỏ dòng `from legacy_v11 import ...`.
- Test đổi vì luật mới: `test_lat0_v11.test_so_chuan_v11` kiểm `contract_version` `"1.1"` → `"1.2"` (số chuẩn giữ nguyên).
- File kho làm tròn `fresh` 3 chữ số như JSONL (`items.to_file`) để file **khớp** `gather_end.inventory` (PRD-0 mục G); vẫn đọc lại đúng đơn vị 1/240.
  `test_lat0_v12.test_smoke_ban_giao_file...`: đưa `assertEqual(end["inventory"], saved)` về **sau** khi gán `end`/`saved` (trước đó đứng trước, gây `UnboundLocalError`).
- Kiểm v1.2 trên manifest thật: `test_lat0_v12`, `test_quan_p3`, `test_day_p2`, `test_fresh_p3` (QA, không cần `CHONOI_CONTRACT`).
- `test_fresh_p3.PauseFresh` (AC-P3-10): input cũ THẢ nút pause để tiếp tục, trong khi Ticket-02 4.2 cần cạnh lên kế tiếp — đổi input thành hai lần nhấn (`press`), assert giữ nguyên. `test_lat0_v12` ngất: hàng mất đã hao 1 bước.
- Kết quả: 233 test OK, QA Phase 3 28/28 trên manifest v1.2 thật (`docs/proof/phase-3/enable-v12.txt`).
