# Ma trận truy vết Phase 1

> **Lưu ý:** PRD-0 chưa mở nên chỉ CON-01..03, MOVE-01..03, INV-01 là ID lấy từ tên smoke test có sẵn. Các dòng `(tạm)` / `(chưa có ID)` là ID tạm do TV5 đặt theo bảng vai trò — **phải đối chiếu lại với ID chính thức khi PRD-0 mở**. Bằng chứng hiện chỉ là baseline của starter (branch NguyenMinhPhuc @ f0a1906).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| CON-01 — chạy 0 tick vẫn có dòng kết thúc | `tests/test_smoke_p1.py::Contract::test_con_01_ticks_zero_and_end_line` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| CON-02 — cùng seed/input → output trùng từng byte | `tests/test_smoke_p1.py::Contract::test_con_02_deterministic_bytes` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| CON-03 — input sai → exit 2 (kể cả mode cũ/tương lai) | `tests/test_smoke_p1.py::Contract::test_con_03_bad_input_exit_2`, `tests/test_smoke_p1.py::Contract::test_con_03_old_and_future_modes_rejected` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| MOVE-01 — tốc độ bơi = swim_speed sau ramp | `tests/test_smoke_p1.py::Movement::test_move_01_swim_speed_after_ramp`, `tests/test_smoke_p1.py::Movement::test_move_ramp_doi_huong_trong_tran` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| MOVE-02 — heading dương là đi xuống | `tests/test_smoke_p1.py::Movement::test_move_02_heading_positive_is_down` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| MOVE-03 — chặn ở mép vùng nước, vận tốc về 0 | `tests/test_smoke_p1.py::Movement::test_move_03_edge_clamp`, `tests/test_smoke_p1.py::Movement::test_move_mep_vel_ve_0` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| INV-01 — gather ghi kho, quan đọc kho; hết tick trước thì không ghi | `tests/test_smoke_p1.py::Integration::test_inv_01_gather_writes_inventory_quan_reads_it`, `tests/test_smoke_p1.py::Integration::test_inv_01_not_written_when_tick_limit_first` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| (chưa có ID) — snapshot gather có đủ trường | `tests/test_smoke_p1.py::Contract::test_gather_snapshot_has_gather_fields` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| (chưa có ID) — hết giờ thì kết thúc gather, giữ giỏ | `tests/test_smoke_p1.py::Movement::test_time_ends_gather_and_keeps_hold` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| (chưa có ID) — schema kho sai → exit 2 | `tests/test_smoke_p1.py::Integration::test_inv_bad_schema_exit_2` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| (chưa có ID) — kịch bản ngoài miền / xung đột kho với kịch bản | `tests/test_smoke_p1.py::Contract::test_scenario_out_of_domain_exit_2`, `tests/test_smoke_p1.py::Integration::test_inventory_and_scenario_stock_conflict` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| (chưa có ID) — sai mode / fixture quan không hợp lệ → exit 2 | `tests/test_smoke_p1.py::Integration::test_inventory_flags_mode_mismatch_exit_2`, `tests/test_smoke_p1.py::ScenarioModes::test_khoi_sai_mode_exit_2`, `tests/test_smoke_p1.py::ScenarioModes::test_quan_fixture_khong_hop_le_exit_2`, `tests/test_smoke_p1.py::ScenarioModes::test_quan_player_vel_hop_le` | `docs/proof/phase-1/baseline-smoke.txt` | đạt (baseline starter) |
| AC-P1-G01 (tạm) — oxy giảm khi lặn, nạp lại ở mặt nước | `tests/test_rules_p1.py` + `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl` | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G02 (tạm) — ngạt khi oxy = 0, mất Máu theo choke_interval_ticks | `tests/test_rules_p1.py` + headless gather | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G03 (tạm) — Máu về 0 → ngất, mất giỏ | `tests/test_rules_p1.py` + headless gather | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G04 (tạm) — hái nút ở mặt nước (node_yield, regrow_s) | `tests/test_rules_p1.py` + headless gather | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G05 (tạm) — bắt cá dưới nước (catch_radius, cooldown, fish_yield) | `tests/test_rules_p1.py` + headless gather | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G06 (tạm) — giỏ đầy (hold_capacity) không nhận thêm | `tests/test_rules_p1.py` + headless gather | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-G07 (tạm) — kho ghi đúng một lần ở gather_end | `tests/test_rules_p1.py` + headless gather `--inventory-out` | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q01 (tạm) — khách đến theo lịch (first_customer_tick, customer_interval_s) | `tests/test_rules_p1.py` + `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl` | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q02 (tạm) — hết patience → khách bỏ đi, uy tín −0.5 | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q03 (tạm) — uy tín kẹp trong [0, 5] | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q04 (tạm) — nấu theo menu (recipe, cook_s) | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q05 (tạm) — tối đa một interact mỗi tick | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q06 (tạm) — mang tối đa 1 món (carry_limit) | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |
| AC-P1-Q07 (tạm) — phục vụ: thu đúng price, tip 20% khi đủ điều kiện | `tests/test_rules_p1.py` + headless quan | | chưa đạt — chờ code TV1–TV4 |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Chỉ có baseline của starter: 32/32 test xanh (``docs/proof/phase-1/baseline-smoke.txt``), phủ hợp đồng CLI/JSONL (CON-01..03), di chuyển (MOVE-01..03), kho (INV-01) và các kiểm lỗi đầu vào. Toàn bộ luật gather (oxy, ngạt, Máu, ngất, hái, bắt cá, giỏ) và quan (khách, patience, uy tín, nấu, phục vụ, tip) **chưa đạt** — chưa có code luật, `tests/test_rules_p1.py` đang viết, chưa có bằng chứng.
- Điều cần chỉnh cho phase sau: Khi PRD-0 mở, thay toàn bộ ID tạm bằng ID chính thức; chốt các câu hỏi trong `docs/clarify.md` rồi chỉnh test theo; sau khi TV1–TV4 merge luật, chạy lại test + headless và lưu output vào `docs/proof/phase-1/`.
