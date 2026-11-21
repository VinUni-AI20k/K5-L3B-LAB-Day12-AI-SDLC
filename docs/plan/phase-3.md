# Kế hoạch Phase 3 (Ticket-03 "Mùa Nước Nổi", change request, 1:55–2:30)

Người ghi: Võ Hồng Lương (D, Integrator). Nguồn: Ticket-03 trên lab board (số mục là số mục trong Ticket-03). Không chép lại số liệu của đề; số chuẩn nằm trong `game.contract.json` v1.2 sau việc P3-02. Trạng thái từng việc ở Google Sheet, tab "Phân công" (dòng P3-xx).

## Đây là gì

Một **change request làm vỡ schema**: kho đếm theo loại (`{"items": {"ca_loc": 2}}`) thành **kho cá thể có độ tươi** (`{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`). Hàng hao tươi theo thời gian, cá thể ươn (`fresh < 30`) chiếm ô nhưng không nấu được, giữ chỗ theo id, giá món theo độ tươi. `contract_version: "1.2"`. Ticket tự nhận 35 phút và yêu cầu `main` luôn chạy được trong lúc chuyển.

## Quyết định (ghi trước khi code, mục 3 của đề yêu cầu)

1. **Schema kho mới thay hoàn toàn schema cũ ở v1.2.** Bên đọc chọn schema theo `contract_version`. Ở v1.2, file kho dạng đếm hoặc sai schema thì **mã 2**. Ở v1.1 vẫn dùng schema đếm (để hồi quy Phase 1–2 còn chạy).
2. **Adapter ở biên, không rải khắp code.** Thêm một hàm đổi qua lại giữa kho đếm và kho cá thể trong `chonoi/inventory.py`; sim bên trong dùng cá thể. Hồi quy Phase 1–2 chạy qua adapter.
3. **Đếm độ tươi chính xác.** Dùng số nguyên (đơn vị nhỏ nhất, ví dụ 240 đơn vị mỗi điểm tươi theo gợi ý của đề), không dùng số thực; ngưỡng 30 và `floor` giá phải đúng từng tick.
4. **Id cá thể:** `I1, I2, …` theo thứ tự vào giỏ, tăng xuyên pha và Ngày, kể cả khi cá thể cũ đã dùng hoặc bỏ; mất hàng theo LIFO vẫn theo thứ tự vào giỏ.
5. **Thứ tự tích hợp để `main` luôn chạy được:** (a) P3-02 schema, adapter và migration test vào `main` trước, bật v1.2 sau cùng; (b) gather và quán làm song song, mỗi người một file; (c) HUD chỉ đọc snapshot; (d) bật `contract_version: "1.2"` khi cả hai đầu bàn giao sẵn sàng (mục 3.2 của đề cho phép chạy hai phiên bản nội bộ trong lúc chuyển).
6. **Mở rộng (dòng nước lũ, khách đặt trước) là tùy chọn;** chỉ làm khi lõi và bằng chứng đã xong. Nhóm 4 người không bắt buộc.

## Phân tích tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Schema, adapter, contract | `chonoi/inventory.py` (file khóa), `game.contract.json` (`freshness`, v1.2), `chonoi/contract.py`, `chonoi/scenario.py` (`gather.hold`, `quan.stock`, `customers[].reserved` là mảng cá thể) | `tests/test_smoke_p1.py` (kho đếm), `tests/test_scenario_contract.py`, `tests/test_contract_v11.py`, `tools/smoke_phase1.py` | D |
| Gather | `chonoi/sim/gather.py`, `chonoi/sim/monsters.py` (`lost` là mảng cá thể) | `tests/test_gather_rules.py`, `tests/test_gather_prd.py`, `tests/test_p2_*` của gather | A |
| Quán | `chonoi/sim/quan.py` (giữ chỗ theo id, hao kho, `spoiled`, giá theo độ tươi, `cook_started.items`) | `tests/test_quan_slice3.py`, `tests/test_quan_slice4.py`, `tests/test_quan_rules.py` | B |
| `day` và Shop | `chonoi/sim/day.py` (bàn giao trong cùng tick; hàng thô của Shop không hao) | test `day` của Phase 2 | A (sau gather) |
| HUD | `chonoi/web/index.html`, `chonoi/live.py` (độ tươi, hàng ươn, đơn bị ảnh hưởng) | `tests/test_live.py` | C (dự phòng D) |
| Hợp đồng, nhật ký thay đổi | `docs/contracts/README.md`, `CHANGELOG.md` (mới; ghi breaking change), `docs/proof/phase-3/`, `docs/verification/phase-3.md` | không | D |

## Việc, người, phụ thuộc (mã AC theo Sheet)

| AC | Việc | Người | Phụ thuộc |
|---|---|---|---|
| AC-P3-01 | Schema kho cá thể, adapter đếm ↔ cá thể, `contract_version` 1.2 và khối `freshness`, migration test | D | không (làm trước) |
| AC-P3-02 | Gather: giỏ cá thể, hao 0.5/s, `spoiled`, `lost` theo cá thể, `gather_end.inventory` cá thể | A | AC-P3-01 |
| AC-P3-03 | Quán: kho cá thể, hao 0.25/s, giữ chỗ theo id, nhả và thử giữ lại một lần, giá theo độ tươi | B | AC-P3-01 |
| AC-P3-04 | `day`: bàn giao cùng tick, Shop không hao hàng thô | A | AC-P3-02, AC-P3-03 |
| AC-P3-05 | HUD hiển thị độ tươi, hàng ươn, đơn bị ảnh hưởng | C | AC-P3-01 |
| AC-P3-06 | Smoke bàn giao kho ở phút 20 (fresh 100 và fresh 30, hai tiến trình) | D | AC-P3-02, AC-P3-03 |
| AC-P3-07 | Hồi quy P1–P2, `CHANGELOG.md`, bằng chứng, `docs/verification/phase-3.md`, tag | D | tất cả |

Lịch (theo Ticket-03): phút 0–7 phân tích và chốt quyết định (bản này), 7–25 viết schema/adapter, gather, quán, HUD song song (smoke phút 20), 25–32 bật v1.2, smoke `day`, hồi quy, CHANGELOG, tag, retro nhanh, 32–35 dự phòng; `phase-3` chậm nhất 2:30.

## Rủi ro

- **Đổi schema chạm gần như mọi test** của gather và quán: người sửa luật cũng sửa test của mình trong cùng PR, ghi lý do thay đổi test.
- **Sai số đếm độ tươi** ở ngưỡng 30 hoặc khi `floor` giá: dùng số nguyên và test đúng tick biên (đề đo tick của event biên phải chính xác).
- **Giữ chỗ theo id** phức tạp hơn giữ theo số lượng (nhả toàn bộ rồi thử giữ lại đúng một lần): B cần đọc kỹ bảng "Độ tươi, giữ chỗ và giá" trong đề.
- **35 phút rất ngắn và D giữ nhiều việc** (schema, smoke, hồi quy, tag): chia `day` cho A, test quán cho B, HUD cho C.
- **C chưa đóng góp ở Phase 1:** nếu HUD trễ thì D nhận (người dự phòng); HUD không chặn tag vì chỉ đọc snapshot.
- **Hồi quy Phase 1–2:** một số test cũ đổi theo schema; mọi thay đổi test phải có lý do trong commit, `CHANGELOG.md` và ma trận truy vết.

## Câu hỏi cho PO / `docs/clarify.md`

- Dùng đơn vị số nguyên nào cho độ tươi (đề gợi ý 240 đơn vị mỗi điểm) và `fresh` trong file là số thực hay số nguyên?
- Hàng ươn có bị Shop mua lại, hoặc bán ở Shop không (Shop và Chợ Chú Sáu là mở rộng)?
- Khi nhả phần giữ vì ươn và không giữ lại đủ, thứ tự xử lý các đơn (theo `order_tick` rồi id bàn) áp dụng thế nào trong cùng tick?
