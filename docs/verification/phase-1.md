# Ma trận truy vết Phase 1

Kiểm chứng mới nhất chạy trên `Quoosc` tại `e9a9c12`; proof script báo 201 test OK (5 expected failures thuộc DaySim/Runner) và headless 9/9 bước đạt. Xem [verify-run.txt](../proof/phase-1/verify-run.txt).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| G1: oxy, ngạt, máu, ngất | Unit test oxy cạn, choke, faint | `tests.test_p1_logic.GatherLogic.test_empty_oxygen_chokes_and_faints` + full suite | đạt |
| G2: hái, bắt cá, giỏ LIFO | Test hái/bắt, hold_full, regrow | `tests.test_p1_logic.GatherLogic.test_harvest_lifo_and_hold_full`, `tests.test_p1_g2` | đạt |
| G2: kho, cập bến, cộng dồn | Integration headless và live persistence | `tests.test_smoke_p1.Integration`, `tests.test_live.LiveInventoryPersistenceTest` | đạt |
| Q3: khách, giữ chỗ, kiên nhẫn, ID/lịch | P1 Q3 fixtures, reservation, patience, replay, validation | [`Q3 proof`](../proof/phase-1/q3/README.md), `tests.test_p1_q3` | đạt theo quyết định PO; mapping tới ticket/Test Contract gốc vẫn provisional |
| Q4: nấu, bưng, phục vụ, tiền, ưu tiên tương tác | Lat 4 unit tests | [`quan-lat4-test.txt`](../proof/phase-1/quan-lat4-test.txt) | đạt theo tests; Q4-F1 orphan dish còn là finding riêng |
| Headless gather/quán | Cùng seed replay, sample inventory, invalid input exit 2/no output | [`verify-run.txt`](../proof/phase-1/verify-run.txt) | đạt, 9/9 bước, exit 0 |
| Contract D fixture tay/assigned | QA fixture cho `hand=null`, assigned order thiếu món | [`qa-contract-tests.txt`](../proof/phase-1/qa-contract-tests.txt) | chưa đạt trong lần QA được ghi; cần quyết định/fixture mới trước khi tuyên bố AC đạt |
| HUD hoàn chỉnh | Live UI review | `chonoi/web/index.html`; phase UI proof ở Phase 2 | Phase 1 chỉ xác nhận khung HUD đọc snapshot, không xác nhận hoàn thiện đồ họa |

## Đánh giá ngắn

- Các hành vi luật P1 Gather, Q3 customer/reservation/patience, Q4 cook/serve và kho có unit/integration coverage; full suite đang pass.
- `verify_phase1.py` chạy thật trên commit `e9a9c12`, Python 3.11.9 Windows; shim xử lý alias `python3` của Microsoft Store, không sửa contract.
- Ticket gốc PRD-0/Test Contract không có đầy đủ trong checkout. Q3 decisions đang được đối chiếu theo PO clarify; không tuyên bố giảng viên đã nghiệm thu.
- Năm expected failures trong full suite là regressions DaySim/Runner của Phase 2, không phải expected pass cho AC Phase 1.
