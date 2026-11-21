# Ma trận truy vết Phase 1

Kiểm chứng mới nhất được thực hiện sau khi hòa nhập `origin/main` (`726d101`) vào `main` tại `d754125`. Bộ xác minh Phase 1 đạt 9/9 bước; full suite có 225 tests, không fail/error/expected failure. Log mới nhất: [verify-run.txt](../proof/phase-1/verify-run.txt).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| G1: oxy, ngạt, máu, ngất | Unit test oxy cạn, choke, faint | `tests.test_p1_logic.GatherLogic` + full suite | Đạt |
| G2: hái, bắt cá, giỏ LIFO | Test hái/bắt, hold_full, regrow | `tests.test_p1_logic.GatherLogic`, `tests.test_p1_g2` | Đạt; kho vật lý theo contract 1.3 |
| G2: kho, cập bến, cộng dồn | Headless gather → inventory → quan; legacy v1.1 có test riêng | `tests.test_smoke_p1.Integration`, `tests.test_live.LiveInventoryPersistenceTest` | Đạt |
| Q3: khách, giữ chỗ, kiên nhẫn, ID/lịch | Fixtures, reservation, patience, replay, validation | [`Q3 proof`](../proof/phase-1/q3/README.md), `tests.test_p1_q3` | Logic và validator đạt theo các quyết định PO được ghi; một số đối chiếu ticket gốc còn provisional |
| Contract D: `hand: null` | Scenario v1.3 chấp nhận tay rỗng; kiểm tra ID reservation duy nhất | `tests.test_p3_v13_integration.ContractV13InventoryTests.test_v13_scenario_checks_unique_reservation_ids_and_accepts_null_hand` | Đạt |
| Contract D: assigned thiếu món / mâu thuẫn state | Không tự suy diễn semantics nghiệp vụ ngoài contract | `tests.test_p1_q3` và `docs/clarify.md` | Chưa xác nhận; cần PO chốt nguồn chuẩn |
| Headless | Replay, sample inventory, input sai exit 2/không ghi file | [`verify-run.txt`](../proof/phase-1/verify-run.txt) | Đạt, 9/9 bước, exit 0 |
| HUD hoàn chỉnh | Live UI review | Phase UI proofs | Phase 1 chỉ xác nhận HUD đọc snapshot; không tuyên bố review UI mới |

## Đánh giá

- Full suite sau cập nhật: 225 tests, tất cả pass; bộ xác minh đạt 9/9 bước, gồm headless deterministic cho Gather/Quán; [log](../proof/phase-1/verify-run.txt).
- Root contract v1.3 được chuyển vào tuning; file inventory count bị từ chối theo schema v1.3. Test legacy chỉ dùng version 1.1 tường minh.
- Theo xác nhận của người dùng, `inventory.json` đã chuyển sang schema Item v1.3; số lượng từng loại được giữ nguyên, cấp ID ổn định `I1`–`I33`, độ tươi khởi tạo 100.
- Ticket PRD-0/Test Contract gốc không có trong checkout. Kết quả kỹ thuật không thay cho xác nhận PO/giảng viên các semantics chưa có nguồn chuẩn.
