# ADR-0001: Kho cá thể có độ tươi (Contract v1.2, TICKET-03 "Mùa Nước Nổi")

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21 (Phase 3, phút 0–7), Integrator NgChiVinh; cả nhóm đọc trước khi code

## Bối cảnh
TICKET-03 thay kho đếm `{"items":{kind:n}}` bằng kho cá thể `{"items":[{id,kind,fresh}]}`; độ tươi hao theo tick
(giỏ 0.5/s, kho quán 0.25/s), ươn khi < 30, giữ chỗ theo id, giá theo độ tươi. Đổi này chạm mọi module dùng kho:
file kho, giỏ gather, kho/giữ chỗ/nấu của quán, bàn giao trong day, scenario, JSONL, HUD và nhiều test P1–P2.

## Các lựa chọn đã cân nhắc
1. **Biểu diễn độ tươi:** (a) float — sai số tích lũy làm lệch nhánh ở ngưỡng 30; (b) số nguyên 240 đơn vị/điểm
   (PRD gợi ý) — chỉ chính xác khi fixture là bội của 1/240; (c) **`fractions.Fraction`** — chính xác với mọi fixture
   (float JSON chuyển thành phân số đúng giá trị nhị phân), hao 1/120 điểm/tick ở giỏ và 1/240 ở quán.
2. **Chuyển phiên bản:** (a) hỗ trợ v1.1 và v1.2 song song theo `contract_version` — tốn thời gian, 35 phút;
   (b) **nhánh tích hợp `v1.2`**: các lát làm trên nhánh này, `main` giữ v1.1 chạy được, bật v1.2 trên `main` bằng
   một lần merge khi cả hai đầu bàn giao (file + day) và regression đã xanh.

## Quyết định
- Độ tươi lưu nội bộ bằng `Fraction`; xuất ra JSONL/snapshot là `float` (JSONL làm tròn 3 chữ số, dung sai ±0.01);
  **file kho ghi float đầy đủ** (`json.dump` không làm tròn) để đọc lại giữ giá trị và nhánh ở ngưỡng.
- Module mới `chonoi/items.py` (adapter) dùng chung: dựng/kiểm cá thể, hao tươi + phát `spoiled` theo id, chọn
  "tươi nhất rồi id nhỏ", chuyển ra JSON. `chonoi/inventory.py` đọc/ghi schema v1.2; kho đếm → mã 2.
- Id cá thể `I1, I2, …` cấp bằng `IdAllocator` (tiền tố `I`), một allocator cho cả lượt (xuyên pha và Ngày);
  id trong fixture/file kho được `reserve`.
- Contract: `contract_version: "1.2"`, thêm `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25,
  spoiled_below:30}`; số chỉ đọc từ đây.
- Tích hợp trên nhánh `v1.2`, theo thứ tự dưới; mỗi bước chạy cả bộ test trên nhánh; `main` chỉ nhận v1.2 qua PR
  cuối (bài học retro Phase 2: Integrator chạy test + bằng chứng trên đúng commit sẽ gắn tag).

## Thứ tự tích hợp
1. Adapter: `items.py`, `inventory.py`, contract v1.2 + `freshness`, `contract.py`, scenario (hold/stock/reserved là
   mảng cá thể) — **NgChiVinh** (phút 7–12).
2. Song song trên nhánh `v1.2` sau bước 1:
   - Lặn — giỏ cá thể, hao 0.5/s, `spoiled`(hold), hái/bắt tạo cá thể fresh 100, `lost` là mảng cá thể (LIFO),
     `gather_end.inventory` v1.2.
   - Quán — kho cá thể hao 0.25/s, `spoiled`(stock) theo id rồi mới xử lý giữ chỗ bị ươn (nhả + thử giữ lại 1 lần,
     không đủ → `unfulfillable`), giữ theo id (tươi nhất, hòa id), giá `floor(niêm yết × fresh TB / 100)`,
     `cook_started.items` là mảng cá thể sắp kind rồi id.
   - Day — bàn giao trong cùng tick không hao thêm, Ngày kế cấp id mới cho mẫu `gather.hold`.
   - HUD — hiện độ tươi / nhãn ươn ở giỏ và kho.
3. QA: test ngưỡng (fixture PRD fresh 30 → `spoiled` tick 1), giữ lại khi vừa ươn, chốt giá, smoke bàn giao file
   và day; regression P1–P2 sửa fixture sang mảng cá thể (ghi lý do).
4. Bật v1.2 trên `main` (PR từ `v1.2`), chạy lại bằng chứng trên commit đó, CHANGELOG, verification, tag `phase-3`.

## Hệ quả — bảng tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter / schema | `chonoi/items.py` (mới), `chonoi/inventory.py`, `chonoi/contract.py`, `game.contract.json`, `chonoi/scenario.py`, `docs/contracts/` | `test_smoke_p1` (file kho đếm → mã 2, schema mới), `test_python_starter_units` (inventory); thêm `tests/test_items_p3.py` | NgChiVinh |
| Lặn | `chonoi/sim/gather.py` (giỏ, hái, bắt, faint, gather_end), `chonoi/sim/monsters.py` (`lost` cá thể) | `test_gather_lat1/lat2`, `test_gather_fish`, `test_gather_monsters`, `test_monsters_edges` (hold/lost dạng cá thể) | TrungHieuPh (giỏ/hái/bắt), 22520160 (`monster_hit.lost`) |
| Quán | `chonoi/sim/quan.py` (stock, `_available`, giữ chỗ theo id, ươn → giữ lại, giá theo tươi, `cook_started.items`) | `test_quan_lat3`, `test_quan_lat4`, `test_p2_quan_shop`, `test_qa_phase*` (stock/reserved dạng cá thể, base_price) | 22520160 (giữ chỗ/ươn), HoangQuan23112004 (nấu/giá) |
| Day / Shop | `chonoi/day.py`, `chonoi/sim/shop.py` (stock cá thể, không hao) | `test_day_p2` (gather.hold mẫu dạng cá thể) | NgChiVinh |
| HUD | `chonoi/web/index.html`, `tools/hud_check.py` | `hud_check` (thêm kiểm độ tươi hiển thị) | truclamld |
| QA | `tests/test_qa_phase3.py` (mới), `docs/proof/phase-3/`, `docs/verification/phase-3.md` | regression P1–P2 sửa fixture | khoa-asta |

Breaking change cho người dùng file kho/scenario: ghi ở `CHANGELOG.md` (schema cũ → mới, cách đổi fixture).
Mở rộng (`current`, `reservations`) chỉ làm sau khi lõi v1.2 xanh.
