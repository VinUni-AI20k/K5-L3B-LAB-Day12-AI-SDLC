# Ma trận truy vết Phase 1

Mã AC do QA đánh theo PRD-0 (`docs/prd/phase-1.md`): mục F (luật bước), E (sự kiện / snapshot), G (kho), D (fixture), DoD mục 7.
Cách kiểm chứng chung: `python3 tools/run_checks.py` (skill `run-checks`); test `@pending` chạy bằng `QA_STRICT=1`.
Bằng chứng ghi ở commit gắn tag: `docs/proof/phase-1/checks-<commit>.txt`.

Trạng thái: **pending** = test đã viết, chờ lát merge · **đạt** / **chưa đạt** = đã chạy trên `main`.

## Buổi sáng (gather)

| AC | Yêu cầu (PRD-0) | Cách kiểm chứng | Lát | Kết quả |
|---|---|---|---|---|
| AC-P1-01 | Oxy theo d cuối bước: dưới nước −1/tick, mặt nước +6, kẹp [0, max] (F Gather) | `test_gather_p1.Oxygen.test_ac_p1_01_*` | 1 | pending |
| AC-P1-02 | `dive` / `surface` một lần khi đổi phía mặt nước, `data.pos` sau di chuyển (E) | `Oxygen.test_ac_p1_02_*` | 1 | pending |
| AC-P1-03 | `oxygen_empty` khi chạm 0; ngạt lần đầu ở t+59, `choke{hp}`, đếm về 0 (F) | `Oxygen.test_ac_p1_03_*` | 1 | pending |
| AC-P1-04 | Máu 0 → `choke`,`faint{cause,lost LIFO,hp:0}`,`gather_end fainted`, kho rỗng, dừng lượt (F, G) | `Oxygen.test_ac_p1_04_*` | 1 | pending |
| AC-P1-05 | Nổi lên đúng bước đáng lẽ ngạt → hồi oxy, không ngạt (F) | `Oxygen.test_ac_p1_05_*` | 1 | pending |
| AC-P1-06 | Hái ở mặt nước: nút ready gần nhất (tính mép), hòa theo id, `gather`, `regrow_ticks=1200`, `node_regrown` (F) | `Gathering.test_ac_p1_06_*` | 2 | pending |
| AC-P1-07 | Không hái dưới nước / ngoài bán kính / nút chưa ready (F) | `Gathering.test_ac_p1_07_*` | 2 | pending |
| AC-P1-08 | Giỏ đầy khi hái → `hold_full{action:gather,node_id,required,free}`, nút giữ nguyên (E, F) | `Gathering.test_ac_p1_08_*` | 2 | pending |
| AC-P1-09 | Bắt cá dưới nước: đàn gần nhất, hòa id (F2 < F10), `fish_caught`, xóa đàn, hồi 30 tick dùng lại từ t+L (F) | `Catching.test_ac_p1_09_*` | 2 | pending |
| AC-P1-10 | Không bắt ở mặt nước / ngoài tầm; thiếu chỗ → `hold_full`, giữ đàn, không thử đàn khác (F) | `Catching.test_ac_p1_10_*` | 2 | pending |
| AC-P1-11 | Cập bến xét trước hái, tính đúng mép bán kính; kho = `gather_end.inventory` (F, G) | `DockAndInventory.test_ac_p1_11_*` | khung | đạt (local, chưa ở commit tag) |
| AC-P1-12 | Hái hợp lệ ở bước cuối vẫn vào kho, kết thúc `time` (F) | `DockAndInventory.test_ac_p1_12_*` | 2 | pending |

## Buổi tối (quan)

| AC | Yêu cầu (PRD-0) | Cách kiểm chứng | Lát | Kết quả |
|---|---|---|---|---|
| AC-P1-20 | Khách đầu ở `first_customer_tick`, `customer_arrived`, giữ chỗ đúng công thức, kiên nhẫn giảm từ bước sau (F Quán) | `test_quan_p1.Customers.test_ac_p1_20_*` | 3 | pending |
| AC-P1-21 | Chỉ chọn món đủ kho khả dụng (mọi seed) (F) | `Customers.test_ac_p1_21_*` | 3 | pending |
| AC-P1-22 | Không món → `no_dish {}`; hết bàn → bỏ lượt; lịch mỗi 900 tick (F) | `Customers.test_ac_p1_22_*` | 3 | pending |
| AC-P1-23 | Hết kiên nhẫn → `customer_left patience`, uy tín −0.5, nhả giữ chỗ, bàn trống (F) | `Customers.test_ac_p1_23_*` | 3 | pending |
| AC-P1-24 | Bếp idle → `cook_started{items,base_price}`, trừ kho, đơn `assigned` (F, E) | `Kitchen.test_ac_p1_24_25_*` | 4 | pending |
| AC-P1-25 | Nấu xong `dish_ready`; bếp ready + tay trống → `dish_picked`, `hand` = payload (F) | `Kitchen.test_ac_p1_24_25_*` | 4 | pending |
| AC-P1-26 | Phục vụ đúng đơn → `served`, khách ăn 600 tick; phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ (F) | `ServeAndPay.test_ac_p1_26_*` | 4 | pending |
| AC-P1-27 | Ăn xong `paid`, boa = floor(giá × 0.2) nếu kiên nhẫn ≥ 50%, uy tín +0.2; điểm = earned + 100×floor(uy tín) (F, E) | `ServeAndPay.test_ac_p1_26_27_*`, `test_ac_p1_27_*` | 4 | pending |
| AC-P1-28 | Hết ca: khách chờ rời `closing` không trừ uy tín, khách ăn trả `closing`, `quan_end` (F) | `Closing.test_ac_p1_28_*` | 3+4 | pending |
| AC-P1-29 | Fixture quán mâu thuẫn (món lạ, giữ khác công thức / quá tồn, tay và đơn lệch) → mã 2, không ghi output (D) | `FixtureValidation.test_ac_p1_29_*` | 4 | pending |
| AC-P1-30 | Quán cùng seed + kho → JSONL giống từng byte (E) | `Determinism.test_ac_p1_30_*` | khung | đạt (local, chưa ở commit tag) |

## Test Contract và DoD

| AC | Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|---|
| AC-P1-40 | Smoke hai tiến trình: quán tick 0 có `stock` đúng file kho (G) | `run_checks.py` bước "smoke hai tiến trình" + `test_smoke_p1` (`test_inv_01_*`) | đạt (local, chưa ở commit tag) |
| AC-P1-41 | Cùng seed → JSONL gather giống từng byte (E) | `run_checks.py` bước "tất định" + `test_con_02_*` | đạt (local, chưa ở commit tag) |
| AC-P1-42 | Mã thoát 0/1/2, cờ sai / fixture sai → 2 trước khi ghi (B, C, D) | `test_smoke_p1.Contract`, `ScenarioModes` | đạt (local, chưa ở commit tag) |
| AC-P1-43 | HUD đọc được: sáng (thời gian, oxy, Máu, giỏ); tối (kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín) | Chơi thử `python3 -m chonoi.live --mode gather` / `--mode quan`, chụp màn hình vào `docs/proof/phase-1/` | chưa kiểm (chờ lát 1–4) |
| AC-P1-44 | TEAM.md đủ người, `team_size` khớp | `run_checks.py` bước "check_team" | chưa đạt (TEAM.md chưa điền) |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: (điền lúc 0:50 trên commit gắn tag)
- Điều cần chỉnh cho phase sau:
