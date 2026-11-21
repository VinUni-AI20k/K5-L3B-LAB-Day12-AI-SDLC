# Ma trận truy vết Phase 3

> `main` sau khi bật contract v1.2 (adapter, gather v1.2, PR #9 quán v1.2, PR #10 LIFO, `day` v1.2, PR #12 HUD tối, test từ PR #11). Tag `phase-3` gắn trên commit chứa file này.
> Tổng: `unittest` 202 OK + 4 skip ([unittest.txt](../proof/phase-3/unittest.txt)) · smoke v1.2 12/12 ([smoke.txt](../proof/phase-3/smoke.txt)) · `day` v1.2 2 Ngày ([day-v12.txt](../proof/phase-3/day-v12.txt)) · tất định 15/15.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-3/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P3-01 kho cá thể qua file | `tests/test_inventory_v12.py::FileV12` (ghi sắp id, đọc lại đúng đơn vị, kho rỗng `{"items":[]}`); v1.2 trả mã 2 cho kho đếm / kind lạ / id trùng / fresh ngoài [0,100] / thiếu khóa | [unittest.txt](../proof/phase-3/unittest.txt), [smoke.txt](../proof/phase-3/smoke.txt) (mục kho sai) | đạt |
| AC-P3-02 contract v1.2 | `contract_version: "1.2"`, `tuning.freshness {100, 0.5, 0.25, 30}`; `contract.py` bắt buộc khối này ở 1.2 | `game.contract.json`, [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-03 độ tươi chính xác ở ngưỡng 30 | `chonoi/items.py` dùng 240 đơn vị/điểm (gather −2, quán −1 đơn vị/tick, ươn < 7200); `test_inventory_v12::Units` (fresh 30 ươn ở bước gather đầu, quán 30.5 ươn đúng tick 121, spoiled theo id, kẹp 0) | [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-10 gather tạo cá thể | `tests/test_gather_v12.py` (hái / bắt tạo cá thể fresh 100, một cá thể mỗi đơn vị yield, hao từ bước sau; id tiếp nối `ItemIds`) | [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-11 ươn trong giỏ | fixture TICKET-03 `fresh 30`, 1 bước → `spoiled {I1, ca_linh, hold}` tick 1; đúng một lần | [smoke.txt](../proof/phase-3/smoke.txt) (mục 1), `test_ticket_fixture_spoils_on_first_step` | đạt |
| AC-P3-12 bàn giao file gather → quan | smoke: dock 3 cá thể → `kho.json` sắp id, fresh sau 1 bước hao; quán `--ticks 0` đúng id / kind / độ tươi như file | [smoke.txt](../proof/phase-3/smoke.txt), `smoke-kho.json`, `smoke-quan.jsonl` | đạt |
| AC-P3-13 tick_limit không ghi kho | smoke mục "tick_limit không tạo file kho" | [smoke.txt](../proof/phase-3/smoke.txt) | đạt |
| AC-P3-20 mất hàng LIFO là mảng cá thể (LyLe10) | `test_gather_survival::test_v12_choke_loss_preserves_individuals_and_lifo`, `test_gather_monster_movement::test_v12_hit_and_fatal_loss_keep_lifo_id_and_fresh`, `test_monster_integration_lyle10::test_day_monster_loss_v12_individuals` (`lost` của `monster_hit` / `faint` theo LIFO, giữ id và fresh sau hao đầu bước) | [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-30 (lát 3) kho quán cá thể | `tests/test_quan_v12_stock.py::StockSchema` (snapshot `stock` là mảng `{id,kind,fresh}` sắp theo id; hàng ươn vẫn trong kho; `ItemIds` nối sau id đã nạp) | [lat3-quan-stock-v12.txt](../proof/phase-3/lat3-quan-stock-v12.txt) | đạt (manifest đã bật v1.2; chạy lại trong unittest.txt) |
| AC-P3-31 (lát 3) hao tươi + ươn | `Decay`, `Spoiled` (0.25/s kể cả hàng giữ, kẹp 0; fresh đúng 30 ươn ở bước đầu; phát `spoiled` location `stock` đúng một lần, nhiều cá thể theo id; hàng ươn không dùng để gọi món → `no_dish`) | như trên | đạt |
| AC-P3-32 (lát 3) giữ chỗ theo id | `ReserveById` (tươi nhất, hòa theo id; bỏ qua hàng ươn; khách sau lấy phần còn lại) | như trên | đạt |
| AC-P3-33 (lát 3) giữ lại khi phần giữ vừa ươn | `ReReserve` (nhả toàn bộ, giữ lại đúng một lần; thiếu → `unfulfillable`, khách chờ tới hết kiên nhẫn, bếp không nấu đơn đó; nhiều đơn theo order_tick rồi id bàn — clarify #17) | như trên | đạt |
| AC-P3-34 (lát 3) fixture v1.2 | `FixtureV12`, `ScenarioFileV12` (reserved mảng id; bỏ trống thì cấp theo order_tick rồi id bàn sau phần giữ tường minh; id không có / đã ươn / khác công thức / dùng chung / đơn không phải reserved mà giữ → mã 2; giá chốt ≤ niêm yết — clarify #18) | như trên | đạt |
| (lát 4 + lát 3) nấu tiêu đúng id, giá theo tươi | `CookWithIds` (`cook_started.items` mảng cá thể sắp kind rồi id, `base_price = floor(giá × TB fresh / 100)`, cá thể đã dùng rời kho) | như trên | đạt — len2412 rà lại phần `_cook_at` |
| AC-P3-35 boa trên giá đã chốt (len2412, từ PR #11) | `test_quan_service::test_cooking_consumes_reserved_ids_and_locks_freshness_price` (giá 111 = floor(120 × 92.5%), boa 22) | [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-40 `day` v1.2 | `tests/test_day_v12.py` + day-v12.txt: bàn giao cùng tick không hao thêm; Ngày 2 cấp id mới I4–I6 theo mẫu; Shop không hao; ngất → `[]` | [unittest.txt](../proof/phase-3/unittest.txt), [day-v12.txt](../proof/phase-3/day-v12.txt) | đạt |
| AC-P3-50 HUD độ tươi | Sáng: thanh độ tươi mỗi ô giỏ, hàng ươn đỏ + ✕, "ươn N"; tối (len2412, PR #12): từng cá thể % / "ƯƠN", hàng ươn tách khỏi kho khả dụng; ngưỡng từ `meta.freshness` | [hud-sang-v12.png](../proof/phase-3/hud-sang-v12.png), `test_live` | đạt (sáng có ảnh chơi thật); **tối chưa có ảnh** |
| AC-P3-60 CHANGELOG + tác động | `CHANGELOG.md` (breaking change, cách sửa fixture); `docs/plan/phase-3.md` (bảng tác động, quyết định schema, thứ tự tích hợp); hợp đồng mục 6 | các file đó | đạt |
| AC-P3-61 regression P1–P2 | toàn bộ test P1–P2 chạy trên v1.2: 202 OK; test đổi vì luật mới có lý do trong commit `cd5c713` (bật v1.2) và `749fdf9` (gather v1.2); 4 test fixture quán kiểu v1.1 skip, thay bằng `FixtureV12` / `ScenarioFileV12` | [unittest.txt](../proof/phase-3/unittest.txt) | đạt |
| AC-P3-62 tất định | 3 seed × 5 kịch bản (gồm `day --days 2`) chạy 2 lần, so byte | [tat-dinh.txt](../proof/phase-3/tat-dinh.txt) | đạt (15/15) |
| AC-P3-70 mở rộng | `burn` (PR #8) chưa rebase lên v1.2; `current` / `reservations` chưa làm | — | **chưa đạt** (dời sang Phase 4; nhóm 5 người cần ≥ 1 mục cả buổi lab) |

## Đóng góp theo người (Phase 3)
- **minhtriet061203:** quán v1.2 (kho cá thể, hao, spoiled, giữ theo id, giữ lại khi ươn, fixture v1.2, nấu tiêu id + giá theo tươi) — PR #9.
- **LyLe10:** `lost` của `monster_hit` / `faint` là mảng cá thể LIFO — PR #10.
- **len2412:** HUD tối độ tươi — PR #12; test giá + boa (chuyển từ PR #11).
- **nglngnguyen-gh (+ Claude):** kế hoạch / tác động / CHANGELOG, adapter `items.py` + file kho v1.2, `day` v1.2, **gather v1.2** (lát của BLong1501 chưa có commit nên Integrator làm thay), bật manifest + chuyển test, HUD sáng, bằng chứng.
- **BLong1501:** chưa có commit ở Phase 3.

## Đánh giá ngắn
- **Đạt:** kho cá thể qua file và trong `day`, kho đếm → mã 2, hao / ươn / spoiled chính xác ở ngưỡng 30, giữ theo id + giữ lại một lần, giá theo tươi + boa, HUD độ tươi hai buổi, regression P1–P2, tất định.
- **Chưa đạt:** mở rộng (burn / current / reservations); ảnh HUD tối khi chơi thật.
- **Điều cần chỉnh cho phase sau:** chia lại việc khi một lát không có commit sau phút 15; rebase PR mở rộng ngay sau khi lõi đổi schema.
