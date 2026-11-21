# Kế hoạch Phase 3 — CR "Mùa Nước Nổi" (Test Contract v1.2)

- **Mục tiêu:** kho cá thể `{id, kind, fresh}` qua file và trong `day`; hao tươi, ươn, giữ chỗ theo id, giá theo tươi; HUD độ tươi; regression P1–P2 còn hiệu lực xanh; tag `phase-3` trước **2:30**.
- **Mốc:** p7 chốt schema + chia việc (file này) · p12 adapter v1.2 lên `main` · p20 smoke bàn giao kho + standup · p25 bật v1.2 + smoke file & `day` + regression · p32 tag.

## Quyết định đổi schema (ghi ADR-lite)

| Quyết định | Chi tiết |
|---|---|
| Biểu diễn độ tươi | **Số nguyên đơn vị**: 1 điểm tươi = 240 đơn vị → fresh 100 = 24000; gather −2/tick (0.5/s), quán −1/tick (0.25/s); ươn khi `< 7200` (30). So ngưỡng bằng số nguyên → không sai số ở 30 (TICKET-03 gợi ý). Chỉ đổi sang `fresh = units / 240` khi xuất snapshot / event / file. |
| Cá thể trong sim | dict `{"id", "kind", "fresh_units"}`; danh sách giỏ giữ **thứ tự vào giỏ** (LIFO khi mất hàng). |
| Cấp id | `ItemIds` (`chonoi/inventory.py`): `I1, I2, …` theo thứ tự vào giỏ, **tăng xuyên pha và Ngày**; reserve các id đã nạp từ scenario / file kho. |
| File kho | v1.2: `{"items":[{"id","kind","fresh"}]}` sắp theo id; đọc chọn schema theo `contract_version`; v1.2 gặp kho đếm / sai schema / kind lạ / id trùng / fresh ngoài [0,100] → mã 2. Ghi tạm + thay thế nguyên tử, `fresh` ghi đủ chính xác (không làm tròn 3 chữ số). |
| Giữ chỗ | `customers[].reserved` = **mảng id**; lấy cá thể khả dụng tươi nhất, hòa theo id. |
| Giá | Lúc bắt đầu nấu: `base_price = floor(giá niêm yết × trung bình fresh / 100)` tính bằng số nguyên đơn vị; boa tính trên giá đã chốt. |
| Chuyển tiếp | Adapter vào `main` trước, **bật `contract_version: "1.2"` cùng commit** với bước chuyển giỏ/kho của gather và quán (p25) để `main` luôn xanh. |

## Phân tích tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter / schema | `chonoi/inventory.py` (đọc/ghi v1.2, `ItemIds`, hàm hao tươi + ươn), `chonoi/contract.py` (khối `freshness`, version 1.2), `game.contract.json`, `chonoi/scenario.py` (hold/stock là mảng cá thể, reserved là mảng id, id vật lý duy nhất), `docs/contracts/README.md` mục 6, `CHANGELOG.md` | Thêm `test_inventory_v12.py`; đổi smoke P1 + `smoke-hai-tien-trinh` sang kho cá thể | **nglngnguyen-gh** |
| Lặn — tạo hàng + hao tươi | `chonoi/sim/gather.py`: hái/bắt tạo cá thể fresh 100, hao giỏ 2 đơn vị/tick ở đầu bước, `spoiled` (location `hold`) theo id, `gather_end.inventory` mảng cá thể; `hold_full` không đổi | Đổi `test_gather_slice2.py` (hold/kho là mảng cá thể); thêm test ngưỡng 30 (fixture TICKET-03) | **BLong1501** |
| Lặn — mất hàng | `gather.py`: `lost` của `monster_hit` / `faint` là mảng cá thể theo LIFO; scenario `gather.hold` mảng cá thể | Đổi `test_gather_survival.py`, `test_gather_monster_movement.py`, `test_monster_integration_lyle10.py` phần `lost` | **LyLe10** |
| Quán — kho + giữ chỗ | `chonoi/sim/quan.py`: stock là mảng cá thể, hao 1 đơn vị/tick kể cả hàng giữ, `spoiled` (location `stock`) theo id, giữ theo id (tươi nhất, hòa id), giữ lại đúng một lần khi phần giữ vừa ươn → không đủ thì `unfulfillable`; fixture `reserved` mảng id | Đổi `test_quan_customers.py`, `test_quan_p2_tables_plan.py` | **minhtriet061203** |
| Quán — nấu + giá | `quan.py`: `_cook_at` tiêu đúng id giữ, `cook_started.items` mảng cá thể (kind rồi id), giá theo tươi, boa trên giá chốt | Đổi `test_quan_service.py`; thêm test chốt giá | **len2412** |
| `day` | `chonoi/day.py`: bàn giao mảng cá thể cùng tick, id tăng xuyên Ngày, Ngày kế cấp id mới cho mẫu `gather.hold`; Shop `stock` mảng cá thể không hao | Đổi `test_day_shop_pause.py` phần kho | **nglngnguyen-gh** |
| HUD | `chonoi/web/index.html`: độ tươi / nhãn "ươn" ở giỏ (sáng) và kho (tối) | `test_live.py` | Long (sáng), Lên (tối) |
| Mở rộng | PR #8 `burn` (Lên) — rebase lên v1.2 sau khi lõi xanh | test của PR | len2412 |

## Thứ tự tích hợp
1. **Adapter** (`inventory.py` + `contract.py` + scenario) lên `main`, vẫn chạy v1.1 → mọi test cũ xanh.
2. Lặn (Long, Ly) và Quán (Triết, Lên) làm song song **trên nhánh từ `main` có adapter**, dùng `ItemIds`, `decay_items()`, `fresh_of()`.
3. p20: gộp Lặn + Quán vào nhánh tích hợp `v1.2`, chạy smoke bàn giao (fixture TICKET-03).
4. p25: `day` + bật `contract_version: "1.2"` + đổi test cũ (ghi lý do) → gộp `main`, chạy regression + skill, bằng chứng, tag.
