# Ma trận truy vết Phase 3 — Q3/Quoosc và trạng thái tích hợp

| AC | Cách kiểm chứng | Bằng chứng | Kết quả trên nhánh Quoosc |
|---|---|---|---|
| AC-P3-01 | `tests.test_p3_inventory` | `inventory-day-test.txt` | Đạt adapter explicit v1.2 và validation; contract mặc định vẫn 1.1, chưa bật end-to-end v1.2 |
| AC-P3-02 | `tests.test_p3_gather`, `tests.test_p3_q3_freshness`, `tests.test_p3_quan_price` | [`q3-freshness.txt`](../proof/phase-3/q3-freshness.txt) | Q3 kho Quán đạt kiểm thử cô lập: exact 0.25/s, clamp, reserved stock vẫn hao; Phase 3 toàn nhóm còn chờ kiểm pause/live integration |
| AC-P3-03 | tests Gather + Q3 threshold fixtures | [`q3-freshness.txt`](../proof/phase-3/q3-freshness.txt) | Q3 đạt: threshold crossing phát `spoiled` đúng một lần, theo ID, location `stock`; không phát lại item đã ở dưới ngưỡng từ đầu |
| AC-P3-04 | freshest-first, ID tie, atomic recipe, spoil/retry and idempotency tests | [`q3-freshness.txt`](../proof/phase-3/q3-freshness.txt) | Q3 behavior đã cài và isolated tests đạt. Tích hợp schema `unfulfillable` còn chờ PO/Integrator (clarify #16); AC chưa nghiệm thu hoàn toàn |
| AC-P3-05 | `tests.test_p3_quan_price` | [`quan-price-test.txt`](../proof/phase-3/quan-price-test.txt) | Đạt; test oracle phản ánh freshness decay trước tương tác theo thứ tự tick Phase 3 |
| AC-P3-06 | Test `faint`/`monster_hit` lost LIFO dạng Item | — | Chưa xác nhận bằng proof của chủ lát/QA |
| AC-P3-07 | smoke hai tiến trình gather→inventory→quan | — | Chưa có proof mới ở nhánh này |
| AC-P3-08 | `tests.test_p3_inventory` day handoff | [`inventory-day-test.txt`](../proof/phase-3/inventory-day-test.txt) | Đạt theo proof Bào: giữ ID/kind/fresh và allocator xuyên ngày |
| AC-P3-09 | live HUD screenshot | — | Chưa có proof mới ở nhánh này |
| AC-P3-10 | full unittest regression | [`phase-1/verify-run.txt`](../proof/phase-1/verify-run.txt) | 189 tests OK, 5 expected failures còn thuộc DaySim/Runner; exit code thật được ghi trong proof |

## Q3 implementation notes

- `QuanSim` giữ `Item` vật lý, hao `freshness.quan_decay_per_s / tick_hz` bằng `Fraction`, không bỏ ID hoặc tăng lại stock khi release.
- Reservation theo recipe nguyên khối, loại hàng dưới ngưỡng, chọn tươi nhất; tie dùng `sort_by_id`. Consume và release có trạng thái idempotent.
- Khi item được giữ vượt ngưỡng ươn, phát `spoiled`, nhả toàn bộ reservation và thử lại một lần. Nếu thiếu item, order giữ trạng thái customer waiting, bỏ reservation, ghi `order_status: unfulfillable` và phát event payload đang đề xuất.
- Event `unfulfillable` chưa có trong shared contract; xem [clarify #16](../clarify.md) và [Q3 handoff](../../specs/002-p3-q3-freshness/handoff.md). Không báo AC-P3-04 là nghiệm thu nhóm.
- `game.contract.json` vẫn ở 1.1; adapter v1.2 có test riêng, nhưng kích hoạt manifest và validation scenario/headless do Integrator/QA phối hợp.
