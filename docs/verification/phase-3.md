# Ma trận truy vết Phase 3 (TICKET-03 · Change Request "Mùa Nước Nổi" · Test Contract v1.2)

- **QA:** `hungdt31` · **Commit được kiểm:** `32883d0` (nhánh `test/p3-qa-changelog-v2` = `main` `39be0e1` + bản sửa của QA) · Python 3.14.4 / Linux.
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → **86/86 OK** ([unittest.log](../proof/phase-3/unittest.log)).
- Bằng chứng smoke: [docs/proof/phase-3/integration.md](../proof/phase-3/integration.md).
- Nguồn AC: [docs/plan/phase-3.md](../plan/phase-3.md) và [docs/clarify.md](../clarify.md) #3–#7. QA chưa đối chiếu trực tiếp nguyên văn TICKET-03; xem mục "Rủi ro".

## 1. Contract & schema kho cá thể

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `contract_version: "1.2"`, khối `freshness` (100 / 0.5 / 0.25 / 30) | Đối chiếu `game.contract.json` | [game.contract.json](../../game.contract.json) | Đạt |
| File kho là mảng cá thể `{id, kind, fresh}`, sắp theo `id`; rỗng là `[]` | `test_freshness_p3::test_inventory_roundtrip_keeps_ids_and_freshness_into_quan`; `test_smoke_p1::test_inv_01_*` | [integration-kho.json](../proof/phase-3/integration-kho.json) | Đạt |
| **Kho đếm cũ → mã 2**; thiếu `fresh`, `fresh` ngoài `[0, 100]`, `id` trùng, `kind` lạ → mã 2 | `test_smoke_p1::test_inv_bad_schema_exit_2`, `test_freshness_p3::test_counted_inventory_and_string_hold_and_counted_stock_exit_2` | [schema-exit2.log](../proof/phase-3/schema-exit2.log) | Đạt |
| Scenario `gather.hold`, `quan.stock`, `customers[].reserved` dạng v1.2, `id` duy nhất | Test của lát scenario + fixture đã chuyển | unittest.log | Đạt |

## 2. Độ tươi ở buổi sáng

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Hao 0.5/s ở đầu mỗi bước | `test_freshness_p3::test_hold_decays_each_tick_and_spoils_strictly_below_threshold_once` | unittest.log | Đạt |
| **Ngưỡng 30**: đúng 30 chưa ươn, < 30 thì ươn; `spoiled {item_id, kind, location: "hold"}` phát một lần | như trên; kiểm đột biến (đổi thành `<= 30` thì test fail) | unittest.log | Đạt |
| Hái hoặc bắt cá: id mới `I<n+1>`, `fresh = 100`, hao từ bước sau | `test_harvest_new_item_gets_next_id_full_freshness_and_decays_from_next_step` | unittest.log | Đạt |
| LIFO và `lost` của `monster_hit` / `faint` theo cá thể | `test_gather_monsters::test_patrol_chase_hit_lifo_recoil_and_invuln` (id `I5, I4`), `test_gather_oxygen::test_faint_*` (id `I3, I2, I1`); smoke day5 có 4 cú hit | [day5-checks.log](../proof/phase-3/day5-checks.log) | Đạt |
| `gather_end.inventory` theo cá thể | smoke tích hợp | [integration-gather.jsonl](../proof/phase-3/integration-gather.jsonl) | Đạt |

## 3. Độ tươi, giữ chỗ, giá ở buổi tối

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Hao 0.25/s ở đầu bước, cả hàng đang giữ, kẹp đáy 0 | `test_freshness_p3::test_quan_decays_slower_than_gather`; `test_quan_fresh_reserve::*` | unittest.log | Đạt |
| Ngưỡng 30 ở quán; `spoiled(stock)` theo `id` | `test_exact_threshold_is_usable_then_spoils_on_next_tick`, `test_spoiled_events_are_ordered_by_id_and_freshness_is_exact_at_boundary`, `test_just_below_threshold_does_not_emit_spoiled_again`; smoke `I40` | unittest.log, [integration.md](../proof/phase-3/integration.md) | Đạt |
| Hàng ươn vẫn trong kho nhưng không bán (`no_dish`) | `test_freshness_p3::test_spoiled_stock_is_kept_but_never_served` | unittest.log | Đạt |
| Giữ chỗ theo `id`: tươi nhất trước, hòa thì `id` nhỏ; đơn chưa khai cấp theo `(order_tick, table_id)` | `test_quan_customers::test_arrival_reserves_stock_*` (`reserved == ["I1"]`), `test_reserved_item_spoils_and_order_reselects_freshest` | unittest.log | Đạt (sau bản sửa crash `760cb34`) |
| **Hàng giữ vừa ươn thì giữ lại đúng 1 lần**; thiếu hàng thì `unfulfillable`, không tiêu kho | `test_reserved_item_spoils_and_order_reselects_freshest`, `test_no_replacement_marks_unfulfillable_without_consuming_stock` | unittest.log | Đạt |
| **Chốt giá theo `fresh`**: `base_price = floor(giá × avg_fresh / 100)`, `items` sắp `(kind, id)`, boa trên giá chốt | `test_quan_price_day_id::test_cook_started_locks_floor_freshness_price_and_tip`; `tools/qa_check_quan_prices.py` trên 4 + 23 món | [integration-prices.log](../proof/phase-3/integration-prices.log), [day5-prices.log](../proof/phase-3/day5-prices.log) | Đạt |

## 4. Vòng ngày

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| **Id `I1..` xuyên Ngày**: Ngày 1 giữ id mẫu, Ngày ≥ 2 cấp id mới, không dùng lại | `test_quan_price_day_id::test_day_preserves_day1_ids_*`, **`test_freshness_p3::test_gather_allocates_new_item_ids_on_day2_without_reusing_day1_ids`** (chạy gather thật); smoke 5 Ngày | [day5-ids.log](../proof/phase-3/day5-ids.log) | **Đạt sau bản sửa `32883d0`** |
| Chuyển pha không hao thêm (kho quán tick 0 == `gather_end`, cả `fresh`) | `tools/qa_check_day.py` cả 5 Ngày | day5-checks.log | Đạt |
| `pause` không làm hao; resume chạy gameplay ngay bước đó | `test_freshness_p3::test_pause_in_day_gather_does_not_decay_hold_and_resume_decays_same_step` | unittest.log | Đạt (đã kiểm ở gather; quán chưa có test riêng) |
| Shop nhận kho dư dạng cá thể | `test_day_shop_pause::test_day_cycle_*` | unittest.log | Đạt (sau bản sửa crash `760cb34`) |

## 5. Regression P1–P2, hiệu năng, tất định

| AC | Cách kiểm chứng | Kết quả |
|---|---|---|
| Test P1/P2 còn hiệu lực với schema v1.2 | 78 test cũ chuyển fixture, ý nghĩa giữ nguyên; lý do ghi trong commit `8da292b` | Đạt (78/78) |
| Smoke nối kho + `day` 5 Ngày (Cá Sấu, Shop, nâng cấp, `day_plan`) | `qa_autoplay` + `qa_check_day` | Đạt |
| Headless 1 Ngày ≤ 20 s | `/usr/bin/time` | Đạt (1 Ngày 0.72 s; 5 Ngày 2.67 s) |
| Tất định | Chạy 2 lần rồi `cmp` | Đạt (giống từng byte) |

## 6. UI / HUD

| AC | Kết quả |
|---|---|
| HUD hiện độ tươi từng cá thể, nhãn **Ươn (< 30)**, báo `spoiled`, giá món thực tế | Code đã merge (`a0613bb`, `ngthanhtamtb`). **QA chưa kiểm thủ công.** |

## Đánh giá ngắn

- **Đạt:** toàn bộ AC lõi v1.2 chạy headless (schema, độ tươi 2 buổi, ngưỡng 30, giữ chỗ và giữ lại, giá chốt, id xuyên Ngày, pause, regression).
- **Bug QA phát hiện và sửa trong lúc kiểm chứng:**
  1. `main` `39be0e1` đỏ 20/78 test (fixture cũ dạng đếm). Đã chuyển sang v1.2, ghi lý do trong `8da292b`.
  2. Quán **crash, exit 1** khi `--inventory` đi cùng scenario có khách chưa khai `reserved`. Snapshot Shop crash khi còn kho dư dạng cá thể (`760cb34`).
  3. Id cá thể **quay về `I1` mỗi Ngày** do lệch giao diện giữa `day.py` và `gather.py` (`32883d0`). Test cũ không bắt được vì không chạy gather thật.
- **Rủi ro / chờ xác nhận:**
  - [clarify #6](../clarify.md): thứ tự "hao đầu bước rồi mới chốt giá". QA đã theo kế hoạch Phase 3 và đổi 2 test (40 → 39, 90 → 89). **PO cần đối chiếu với TICKET-03.**
  - QA chưa có nguyên văn TICKET-03 nên tên và payload event (`spoiled {item_id, kind, location}`) đang lấy theo code và kế hoạch.
  - `fresh` ghi ra dạng float thô (vd. `97.49166666666666`), không làm tròn. Cần đối chiếu ticket.
- **Chưa kiểm:** HUD độ tươi chưa kiểm thủ công; pause trong quán chưa có test riêng.
- **Đề nghị tag:** merge nhánh này rồi gắn `phase-3` tại commit merge, sau khi `main` chạy xanh toàn bộ.
