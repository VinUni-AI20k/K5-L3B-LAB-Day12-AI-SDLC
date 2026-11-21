# Ma trận test hộp đen của QA — Phase 1

Bảng **chi tiết theo từng test** của QA. Mã `AC-P1-xx` ở đây là mã **test** (khớp tên hàm `test_ac_p1_xx_*`), KHÁC với mã AC chủ đề trong ma trận chính thức [`phase-1.md`](phase-1.md) của Integrator; cột "Ứng với" đối chiếu hai bên.
Cách kiểm chứng chung: `python3 tools/run_checks.py` (skill `run-checks`); `python .agents/skills/verify-phase/verify.py --phase 1` để gom bằng chứng.
Bằng chứng ghi ở commit gắn tag: `docs/proof/phase-1/checks-<commit>.txt`.

Trạng thái: lát 1–4 đã merge vào `main`; mọi test dưới đây chạy thật (không còn `@pending`). "đạt (local)" = đã chạy xanh trên nhánh `feat/qa` sau khi merge `main`, chưa có bằng chứng ở commit gắn tag.

## Buổi sáng (gather)

| AC (test) | Yêu cầu (PRD-0) | Cách kiểm chứng | Lát | Kết quả | Ứng với |
|---|---|---|---|---|---|
| AC-P1-01 | Oxy theo d cuối bước: dưới nước −1/tick, mặt nước +6, kẹp [0, max] (F Gather) | `test_gather_p1.Oxygen.test_ac_p1_01_*` | 1 | đạt (local) | AC-P1-04 |
| AC-P1-02 | `dive` / `surface` một lần khi đổi phía mặt nước, `data.pos` sau di chuyển (E) | `Oxygen.test_ac_p1_02_*` | 1 | đạt (local) | AC-P1-07 |
| AC-P1-03 | `oxygen_empty` khi chạm 0; ngạt lần đầu ở t+59, `choke{hp}`, đếm về 0 (F) | `Oxygen.test_ac_p1_03_*` | 1 | đạt (local) | AC-P1-05 |
| AC-P1-04 | Máu 0 → `choke`,`faint{cause,lost LIFO,hp:0}`,`gather_end fainted`, kho rỗng, dừng lượt (F, G) | `Oxygen.test_ac_p1_04_*` | 1 | đạt (local) | AC-P1-06 |
| AC-P1-05 | Nổi lên đúng bước đáng lẽ ngạt → hồi oxy, không ngạt (F) | `Oxygen.test_ac_p1_05_*` | 1 | đạt (local) | AC-P1-05 |
| AC-P1-06 | Hái ở mặt nước: nút ready gần nhất (tính mép), hòa theo id, `gather`, `regrow_ticks=1200`, `node_regrown` (F) | `Gathering.test_ac_p1_06_*` | 2 | đạt (local) | AC-P1-08 |
| AC-P1-07 | Không hái dưới nước / ngoài bán kính / nút chưa ready (F) | `Gathering.test_ac_p1_07_*` | 2 | đạt (local) | AC-P1-08 |
| AC-P1-08 | Giỏ đầy khi hái → `hold_full{action:gather,node_id,required,free}`, nút giữ nguyên (E, F) | `Gathering.test_ac_p1_08_*` | 2 | đạt (local) | AC-P1-08 |
| AC-P1-09 | Bắt cá dưới nước: đàn gần nhất, hòa id (F2 < F10), `fish_caught`, xóa đàn, hồi 30 tick dùng lại từ t+L (F) | `Catching.test_ac_p1_09_*` | 2 | đạt (local) | AC-P1-09 |
| AC-P1-10 | Không bắt ở mặt nước / ngoài tầm; thiếu chỗ → `hold_full`, giữ đàn, không thử đàn khác (F) | `Catching.test_ac_p1_10_*` | 2 | đạt (local) | AC-P1-09 |
| AC-P1-11 | Cập bến xét trước hái, tính đúng mép bán kính; kho = `gather_end.inventory` (F, G) | `DockAndInventory.test_ac_p1_11_*` | khung | đạt (local) | AC-P1-10 |
| AC-P1-12 | Hái hợp lệ ở bước cuối vẫn vào kho, kết thúc `time` (F) | `DockAndInventory.test_ac_p1_12_*` | 2 | đạt (local) | AC-P1-10 |

## Buổi tối (quan)

| AC (test) | Yêu cầu (PRD-0) | Cách kiểm chứng | Lát | Kết quả | Ứng với |
|---|---|---|---|---|---|
| AC-P1-20 | Khách đầu ở `first_customer_tick`, `customer_arrived`, giữ chỗ đúng công thức, kiên nhẫn giảm từ bước sau (F Quán) | `test_quan_p1.Customers.test_ac_p1_20_*` | 3 | đạt (local) | AC-P1-12 |
| AC-P1-21 | Chỉ chọn món đủ kho khả dụng (mọi seed) (F) | `Customers.test_ac_p1_21_*` | 3 | đạt (local) | AC-P1-12 |
| AC-P1-22 | Không món → `no_dish {}`; hết bàn → bỏ lượt; lịch mỗi 900 tick (F) | `Customers.test_ac_p1_22_*` | 3 | đạt (local) | AC-P1-12 |
| AC-P1-23 | Hết kiên nhẫn → `customer_left patience`, uy tín −0.5, nhả giữ chỗ, bàn trống (F) | `Customers.test_ac_p1_23_*` | 3 | đạt (local) | AC-P1-13 |
| AC-P1-24 | Bếp idle → `cook_started{items,base_price}`, trừ kho, đơn `assigned` (F, E) | `Kitchen.test_ac_p1_24_25_*` | 4 | đạt (local) | AC-P1-15 |
| AC-P1-25 | Nấu xong `dish_ready`; bếp ready + tay trống → `dish_picked`, `hand` = payload (F) | `Kitchen.test_ac_p1_24_25_*` | 4 | đạt (local) | AC-P1-15 |
| AC-P1-26 | Phục vụ đúng đơn → `served`, khách ăn 600 tick; phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ (F) | `ServeAndPay.test_ac_p1_26_*` | 4 | đạt (local) | AC-P1-15 |
| AC-P1-27 | Ăn xong `paid`, boa = floor(giá × 0.2) nếu kiên nhẫn ≥ 50%, uy tín +0.2; điểm = earned + 100×floor(uy tín) (F, E) | `ServeAndPay.test_ac_p1_26_27_*`, `test_ac_p1_27_*` | 4 | đạt (local) | AC-P1-15 |
| AC-P1-28 | Hết ca: khách chờ rời `closing` không trừ uy tín, khách ăn trả `closing`, `quan_end` (F) | `Closing.test_ac_p1_28_*` | 3+4 | đạt (local) | AC-P1-13, 15 |
| AC-P1-29 | Fixture quán mâu thuẫn → mã 2, không ghi output (D): món lạ, giữ khác công thức, giữ quá tồn | `FixtureValidation.test_ac_p1_29_mon_la_*` | 3 | đạt (local) | AC-P1-14 |
| AC-P1-29b | Fixture quán: tay cầm món của đơn `reserved`, đơn `assigned` không có món, món trên tay khác đơn, khách `eating` thiếu timer/giá → mã 2 (D) | `FixtureValidation.test_ac_p1_29_don_va_mon_*` | 3/4 | đạt (local) | AC-P1-14 |
| AC-P1-30 | Quán cùng seed + kho → JSONL giống từng byte (E) | `Determinism.test_ac_p1_30_*` | khung | đạt (local) | AC-P1-02 |

## Test Contract và DoD

| AC (test) | Yêu cầu | Cách kiểm chứng | Kết quả | Ứng với |
|---|---|---|---|---|
| AC-P1-40 | Smoke hai tiến trình: quán tick 0 có `stock` đúng file kho (G) | `run_checks.py` bước "smoke hai tiến trình" + `test_smoke_p1` (`test_inv_01_*`) | đạt (local) | AC-P1-11 |
| AC-P1-41 | Cùng seed → JSONL gather giống từng byte (E) | `run_checks.py` bước "tất định" + `test_con_02_*` | đạt (local) | AC-P1-02 |
| AC-P1-42 | Mã thoát 0/1/2, cờ sai / fixture sai → 2 trước khi ghi (B, C, D) | `test_smoke_p1.Contract`, `ScenarioModes` | đạt (local) | AC-P1-01 |
| AC-P1-43 | HUD đọc được: sáng (thời gian, oxy, Máu, giỏ); tối (kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín) | Chơi thử `python3 -m chonoi.live --mode gather` / `--mode quan`, chụp màn hình vào `docs/proof/phase-1/` | chưa kiểm: cần chơi thử `chonoi.live` cả hai buổi và chụp màn hình | AC-P1-16 |
| AC-P1-44 | TEAM.md đủ người, `team_size` khớp | `run_checks.py` bước "check_team" | đạt (local) | AC-P1-17 |

## Ghi chú
- Lát 4 trên `main` kiểm giá chốt khi nấu: đơn `assigned` phải có `base_price` khớp giá món. Fixture của QA đã sửa theo (đúng PRD mục D).
- 3 test skip còn lại thuộc `test_quan_lat3` (cần ≥ 2 bàn, chờ v1.1).
