# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| G1: oxy, ngạt, máu, ngất | Unit test oxy = 0 ở nước sâu; đủ 60 tick ngạt trừ máu; HP=0 mất giỏ và kết thúc | `tests/test_p1_logic.py::GatherLogic.test_empty_oxygen_chokes_and_faints` | đạt |
| G2: hái, bắt cá, giỏ LIFO | Test hái ở mặt nước với giỏ gần đầy, nút mọc lại và sự kiện `hold_full` | `tests/test_p1_logic.py::GatherLogic.test_harvest_lifo_and_hold_full` | đạt |
| G2: ghi kho tức thì | Headless ghi kho ngay sau hái; Live ghi cùng schema sau sự kiện thu hoạch | `tests/test_smoke_p1.py::Integration.test_inv_immediate_after_harvest`, `tests/test_live.py::LiveInventoryPersistenceTest.test_gather_writes_inventory_immediately` | đạt |
| G2: cập bến và xuất kho | Smoke test cập bến tick 0, đọc/ghi kho JSON và Quán nạp kho | `tests/test_smoke_p1.py::Integration.test_inv_01_gather_writes_inventory_quan_reads_it` | đạt |
| Q3: khách, giữ chỗ, kiên nhẫn | Test khách giữ nguyên liệu; hết kiên nhẫn bỏ đi và giảm uy tín | `tests/test_p1_logic.py::QuanLogic.test_customer_leaves_and_reputation_drops` | đạt |
| Q4: bếp, nấu, bưng, thanh toán | Test bếp nhận món, nấu xong, lấy món, phục vụ bàn và cộng tiền | `tests/test_p1_logic.py::QuanLogic.test_reserved_customer_cooks_serves_and_pays` | đạt |
| Hộp đen headless | Chạy gather/quán với seed cố định và JSONL; output determinism, mã 2 cho đầu vào sai | `docs/proof/phase-1/smoke.txt`, `docs/proof/phase-1/verify-run.txt` (skill `phase-1-verification`: 44 test, sha256 2 lần chạy trùng, 3 ca mã 2), `tests/test_smoke_p1.py` | đạt |
| Giao diện HUD | Khung live đọc snapshot oxy/máu/giỏ/kho/bếp/khách; không chứa luật mô phỏng | `chonoi/web/index.html` | đạt |

## Đánh giá ngắn
- Yêu cầu đạt:
  - Gather: di chuyển/chặn biên, oxy, ngạt, HP, hái/bắt cá và giỏ; xuất kho khi kết thúc.
  - Quán: đặt lịch khách, giữ chỗ nguyên liệu, kiên nhẫn, bếp/nấu, bưng, phục vụ, tiền, tip và uy tín.
  - Tích hợp: Gather ghi schema kho, Quán đọc `--inventory`, headless và live dùng cùng mô phỏng.
- Yêu cầu chưa đạt:
  - Chưa có bằng chứng biểu diễn đồ họa/HUD hoàn chỉnh ngoài khung hình khối tạm.
- Điều cần chỉnh cho Phase 2:
  - Bổ sung bằng chứng chạy headless thực tế vào `docs/proof/phase-1/`.
  - Tách test lát thành file theo quy tắc 1 file test/lát nếu đội phân công cần.
