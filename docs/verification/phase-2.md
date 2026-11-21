# Ma trận truy vết Phase 2

> Commit kiểm chứng: `main` sau khi gộp PR #4 (Long), #5 (Triết), #6 (Lên), #7 (Ly) và lát 4 (`day-shop-pause`). Tag `phase-2` gắn trên commit chứa file này.
> Tổng: `unittest` 154/154 OK ([unittest.txt](../proof/phase-2/unittest.txt)) · smoke P1 10/10 ([smoke.txt](../proof/phase-2/smoke.txt)) · tích hợp 6 nguyên liệu ([integration.txt](../proof/phase-2/integration.txt)) · `day` 1 và 3 Ngày ([day.txt](../proof/phase-2/day.txt)) · tất định 15/15 ([tat-dinh.txt](../proof/phase-2/tat-dinh.txt)).
> Lát 4 Phase 1 (PR #2) được gộp đầu Phase 2 sau khi sửa theo review; AC-P1-40…44 nay chạy trong regression (AC-P2-51).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P2-01 | `contract.py` nạp `game.contract.json` v1.1 (6 nguyên liệu, 6 món, `day_plan` = tổng công thức, `shop`, `monsters`); dữ liệu sai → mã 2 | [unittest.txt](../proof/phase-2/unittest.txt) (mọi test nạp preset qua `load_contract`) | đạt |
| AC-P2-02 | Hợp đồng v1.1 `docs/contracts/README.md` mục 5 (dữ liệu theo lát, chuyển pha, sự kiện, inputs) | `docs/contracts/README.md` | đạt |
| AC-P2-10 | `test_gather_p2_fish::InitialSchools` (8 đàn ở 8 điểm khác nhau) | [unittest.txt](../proof/phase-2/unittest.txt) | đạt |
| AC-P2-11 | `FishSwimAndReflect` (1.5 m/s, đổi hướng ở bước 120, phản xạ mép, góc đảo cả hai) | như trên | đạt |
| AC-P2-12 | `FishSpawnAndOrder::test_spawn_at_360_and_respects_cap` | như trên | đạt |
| AC-P2-13 | `test_catch_uses_pre_swim_position`, `test_random_fish_false_stops_swim_and_spawn` | như trên | đạt |
| AC-P2-14 | HUD sáng trong `chonoi/web/index.html` (có "Thủy quái!", "Hết hơi!", độ sâu, giỏ, đã lấy/cần) | `chonoi/web/index.html` | **chưa kiểm chứng**: chưa chơi thử ghi ảnh; chưa đo chữ ≥ 18 px ở 1280×720 |
| AC-P2-20 | `test_gather_monster_movement::MonsterMovement` (patrol, chase ≤ 10 m, rời > 16 m / d < 10, chặn biên + dải độ sâu) | [unittest.txt](../proof/phase-2/unittest.txt) | đạt |
| AC-P2-21 | `MonsterCombat::test_hit_lifo_tie_and_invulnerability`, `test_invulnerability_expires_exactly_at_configured_tick` | như trên | đạt |
| AC-P2-22 | `test_recoil_steps_direction_and_no_hit_on_final_step` | như trên | đạt |
| AC-P2-23 | `test_faint_after_choke_hit_before_time`, `test_fatal_choke_prevents_hit_even_when_invulnerable`, `test_headless_monster_faint_and_inventory` | như trên | đạt |
| AC-P2-24 | `MonsterIntegration::test_day_spawns_and_standalone`; `day` 3 Ngày: M2 chỉ từ Ngày 3 | [unittest.txt](../proof/phase-2/unittest.txt), [day.txt](../proof/phase-2/day.txt) | đạt |
| AC-P2-30 | `test_quan_service::test_two_stoves_each_take_oldest_reserved_order` (B1, B2 mỗi bếp lấy đơn cũ nhất khi `interact`) + luật chọn đối tượng v1.0 | [unittest.txt](../proof/phase-2/unittest.txt) | đạt |
| AC-P2-31 | `tests/test_quan_p2_tables_plan.py::FourTables`, `SixDishes` (preset v1.1 có T1–T4 và 6 món; khách vào T1→T4 theo id; 4 bàn đầy thì bỏ lượt; bàn id nhỏ nhất vừa trống được dùng lại; quán độc lập chọn đủ 6 món qua 80 seed; món mới chỉ khi đủ công thức) + chạy headless quán độc lập kho 6 nguyên liệu | [lat3-quan-tables-plan.txt](../proof/phase-2/lat3-quan-tables-plan.txt) | đạt |
| AC-P2-32 | `DayPlanFilter` (chỉ món trong kế hoạch dù món khác đủ nguyên liệu; chỉ có món ngoài kế hoạch → `no_dish`; lọc kế hoạch rồi mới lọc kho; kế hoạch 1 suất vẫn gọi tiếp 3 suất; cùng seed cùng món; món kế hoạch D1–D5 đều có trong menu; fixture ngoài kế hoạch → `BadInput` (clarify #16)) + `DayModeIntegration` qua `--mode day` (Ngày 1 chỉ gọi món kế hoạch dù kho đủ món khác; chỉ có món ngoài kế hoạch → `no_dish`; khách dựng sẵn ngoài kế hoạch → mã 2) | như trên | đạt (cả `QuanSim` và `--mode day`; đã sửa `day.py` dùng `menu_filter` thay vì cắt menu — trước đó fixture ngoài kế hoạch gây KeyError mã 1) |
| AC-P2-33 | HUD quán: thanh kiên nhẫn đổi màu < 25% (`test_live::test_quan_patience_bar_warns_below_25_percent`); kho khả dụng + trạng thái bếp từ HUD P1 | [unittest.txt](../proof/phase-2/unittest.txt) | **đạt một phần**: chưa chơi thử ghi ảnh, chưa kiểm tiến độ bếp / món đang cầm / cỡ chữ |
| AC-P2-40 | `test_day_shop_pause::DayFlow` (thứ tự đổi pha cùng tick, bàn giao kho trong bộ nhớ, ngất vẫn mở quán kho rỗng, `days_complete`, `tick_limit`); `day` 3 Ngày | [unittest.txt](../proof/phase-2/unittest.txt), [day.txt](../proof/phase-2/day.txt) | đạt |
| AC-P2-41 | `Shop` (đủ đúng giá vẫn mua, `funds`/`max_level`/`unknown`, buy trước `shop_done`, tự đóng sau 600 tick, earned giữ nguyên) | như trên | đạt |
| AC-P2-42 | `test_upgrade_applies_from_next_day`; day.txt: Ngày 1 Máu 3 / oxy 1800, Ngày 2 Máu 4 / oxy 2700 | như trên | đạt |
| AC-P2-43 | `Pause` (gather: chỉ tăng tick ngoài, sim_tick và timer đứng yên; Shop đứng yên, buy khi pause bị bỏ qua) | [unittest.txt](../proof/phase-2/unittest.txt) | đạt (headless). Pause menu trong cửa sổ chơi: chưa có |
| AC-P2-44 | `DayScenario` (9 kiểu scenario sai + `--days` 0/6 + `--days` với gather → mã 2; ghi đè `day_plan` tính lại ingredients) | [unittest.txt](../proof/phase-2/unittest.txt) | đạt |
| AC-P2-45 | Menu chính, DayIntro, EveningIntro, DayResult, Summary, Shop, pause menu trong `chonoi.live` | — | **chưa đạt**: chưa làm; `chonoi.live` chưa chạy `--mode day` |
| AC-P2-50 | Smoke tích hợp `gather --inventory-out → quan --inventory` với đủ 6 nguyên liệu v1.1 | [integration.txt](../proof/phase-2/integration.txt), `integration-kho.json`; [smoke.txt](../proof/phase-2/smoke.txt) | đạt |
| AC-P2-51 | Regression P1 với số chuẩn: toàn bộ test P1 (lát 1–4, smoke P1) chạy trên v1.1; test đổi có ghi lý do trong commit `aa2445e`, `8a20711` | [unittest.txt](../proof/phase-2/unittest.txt) (154/154) | đạt |
| AC-P2-52 | `kiem_tat_dinh.py`: 3 seed × 5 kịch bản (gồm `day --days 2`), 2 lần, so byte | [tat-dinh.txt](../proof/phase-2/tat-dinh.txt) | đạt (15/15) |
| AC-P2-53 | `day --days 1` 22.200 tick: 3,0 s trên máy nhóm; `test_one_day_under_20s` | [day.txt](../proof/phase-2/day.txt) | đạt |
| AC-P2-60 | Mở rộng `burn` | — | **chưa làm** (dời sang Phase 3) |

## Đánh giá ngắn
- **Đạt:** contract v1.1; cá bơi/sinh; Cá Sấu (patrol/chase/hit/recoil/ngất); 2 bếp, 4 bàn, 6 món, lọc món theo kế hoạch; `--mode day` + Shop + pause ở headless; smoke tích hợp; regression P1; tất định; hiệu năng.
- **Chưa đạt:** AC-P2-45 (các màn menu / DayIntro / Shop / pause trong cửa sổ chơi, `chonoi.live` chưa có `day`) → DoD "chơi trọn vòng ngày với menu, pause và HUD" **chưa đạt** ở bản chơi. HUD sáng / quán chưa chơi thử ghi ảnh (AC-P2-14, 33). Chưa có mục Mở rộng (bắt buộc với nhóm 5 người trong cả buổi lab).
- **Rủi ro test ẩn:** clarify #13 (`attack` khi chưa bật mở rộng được bỏ qua thay vì mã 2), #10 (cách chọn 8 đàn đầu ca), #14 (luồng RNG theo Ngày).
- **Điều cần chỉnh cho phase sau:** làm UI vòng ngày trong `chonoi.live` + chơi thử lưu ảnh; làm `burn`; mở PR sớm hơn để tránh dồn 4 PR cuối phase (xung đột `day.py`, `index.html`, file ghi chép).
