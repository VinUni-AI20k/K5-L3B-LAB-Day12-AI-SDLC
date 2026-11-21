# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| G1: oxy, ngạt, máu, ngất | Unit test oxy = 0 ở nước sâu; đủ 60 tick ngạt trừ máu; HP=0 mất giỏ và kết thúc | `tests/test_p1_logic.py::GatherLogic.test_empty_oxygen_chokes_and_faints` | đạt |
| G2: hái, bắt cá, giỏ LIFO | Test hái ở mặt nước với giỏ gần đầy, nút mọc lại và sự kiện `hold_full` | `tests/test_p1_logic.py::GatherLogic.test_harvest_lifo_and_hold_full` | đạt |
| G2: cập bến và xuất kho | Smoke test cập bến tick 0, đọc/ghi kho JSON và Quán nạp kho | `tests/test_smoke_p1.py::Integration.test_inv_01_gather_writes_inventory_quan_reads_it` | đạt |
| Q3: khách, giữ chỗ, kiên nhẫn | Test khách giữ nguyên liệu; hết kiên nhẫn bỏ đi và giảm uy tín | `tests/test_p1_logic.py::QuanLogic.test_customer_leaves_and_reputation_drops` | đạt |
| Q4: bếp, nấu, bưng, thanh toán | Test bếp nhận món, nấu xong, lấy món, phục vụ bàn và cộng tiền | `tests/test_p1_logic.py::QuanLogic.test_reserved_customer_cooks_serves_and_pays` | đạt |
| Q4: Bếp nấu và dish_ready | Unit test `test_stove_cooks_to_ready` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Q4: Tương tác nấu và nhấc món (cook_started, dish_picked) | Unit test `test_interact_cook_started_and_pick` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Q4: Phục vụ bàn và khách ăn trả tiền (served, paid, tip 20%, reputation) | Unit test `test_serve_and_paid_with_tip` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Q4: Phục vụ trễ không nhận được tip | Unit test `test_paid_without_tip_when_patience_low` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Q4: Thứ tự ưu tiên interact (gần nhất, bếp trước bàn) | Unit test `test_interact_priority_stove_before_table` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Q4: Hết ca tối phát sự kiện quan_end | Unit test `test_shift_ends_with_quan_end` | [`quan-lat4-test.txt`](docs/proof/phase-1/quan-lat4-test.txt) | đạt |
| Hộp đen headless | Chạy gather/quán với seed cố định và JSONL; output determinism, mã 2 cho đầu vào sai | `docs/proof/phase-1/smoke.txt`, `tests/test_smoke_p1.py` | đạt |
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
