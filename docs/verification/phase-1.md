# Ma trận truy vết Phase 1

> Nguồn: PRD-0 (mục 2, 7 và Test Contract v1.0 mục A–G). Mã `AC-P1-xx`,
> Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. `smoke:` = `tests/test_smoke_p1.py`, `qa:` = `tests/test_qa_p1.py`.
> Kết quả: ✅ đạt · ❌ chưa đạt · ⏳ chưa kiểm. Chỉ ghi ✅ khi đã chạy ở commit gắn tag `phase-1`.

## Contract & headless (mục A, B, C, D, E)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-01 | `game.contract.json` đủ khóa preset v1.0, số trong dải hợp lệ; `team`, `team_size` đúng thực tế | `tools/check_team.py` + đọc tay preset | `docs/proof/phase-1/check-team.txt` | ⏳ |
| AC-P1-02 | Cờ headless đúng mục B; mã thoát 0/1/2; `--ticks 0` chỉ dựng fixture; dòng `end` luôn cuối | smoke: `test_con_01_*`, `test_con_03_*` | `docs/proof/phase-1/test-run.txt` | ⏳ |
| AC-P1-03 | Cùng seed + đầu vào → JSONL và file kho giống từng byte | smoke: `test_con_02_deterministic_bytes`; qa: chạy lại 2 lần cho cả `gather` và `quan` | TV2: lệnh `cmp` ở [handoff.txt](../proof/phase-1/handoff.txt) | ⏳ (TV2 báo đạt) |
| AC-P1-04 | Inputs: nút chỉ tác động ở cạnh lên; frame chỉ cập nhật trường có mặt; trường sai, kiểu sai, tick lặp/giảm → mã 2 | smoke + qa | `test-run.txt` | ⏳ |
| AC-P1-05 | Scenario sai (khối sai mode, id trùng, ngoài miền, giỏ quá trần, stock + `--inventory`, giữ chỗ sai…) → mã 2, không ghi output | smoke: `ScenarioModes`, `test_scenario_out_of_domain_exit_2`; qa: thêm các ca còn thiếu | `test-run.txt` | ⏳ |
| AC-P1-06 | JSONL: snapshot ở tick 0, bội số `--snapshot-every`, tick dừng; đủ trường chung; `score = earned + 100 × floor(reputation)`; tọa độ 3 chữ số; mảng sắp theo id | smoke: `test_gather_snapshot_has_gather_fields`; qa: kiểm score, sắp id | `gather-seed1.jsonl`, `quan-seed1.jsonl` | ⏳ |

## Gather — lát 1: bơi, oxy, Máu, giỏ (TV1)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-07 | Vận tốc tới `swim_speed × move` trong ≤ 6 tick; chặn mép, triệt vận tốc hướng ra; hướng theo `move` khác 0 gần nhất | smoke: `Movement` | `test-run.txt` | ⏳ |
| AC-P1-08 | Oxy theo d cuối bước: dưới nước −1/tick (kẹp 0), mặt nước (d ≤ 0.5) +6 (kẹp 1800) và reset đếm ngạt; `oxygen_empty` khi từ dương xuống 0 | qa | `test-run.txt` | ⏳ |
| AC-P1-09 | `dive` / `surface` (data `pos`) chỉ phát khi đổi phía biên mặt nước | qa | `test-run.txt` | ⏳ |
| AC-P1-10 | Ngạt: chạm oxy 0 ở t, ở dưới liên tục → `choke` ở t+59, −1 Máu, đặt lại đếm; nổi lên đúng bước đó thì không ngạt | qa | `test-run.txt` | ⏳ |
| AC-P1-11 | Máu về 0 → bỏ giỏ theo LIFO, `faint` (`cause:"choke"`, `lost`, `hp:0`), `gather_end` `fainted` với kho rỗng, dừng bước | qa | `test-run.txt` | ⏳ |
| AC-P1-12 | Giỏ theo thứ tự nhặt (mới nhất cuối), trần `hold_capacity` = 12 | qa | `test-run.txt` | ⏳ |

## Gather — lát 2: hái, bắt cá, cập bến, kho (TV2)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-13 | `interact` xét bến trước (khoảng cách tới `dock_pos`, tính cả đúng mép) → `gather_end` `docked` | smoke: `test_inv_01_*`; qa: đúng mép bán kính; TV2: `test_gather_l2.py::DockAfterGather` | [kho.json](../proof/phase-1/kho.json) | ⏳ (TV2 báo đạt) |
| AC-P1-14 | Hái chỉ ở mặt nước: nút ready gần nhất trong 2.0 m, hòa theo id; +1, `regrow_ticks` = 1200, phát `gather`; thiếu chỗ → `hold_full`, nút giữ nguyên | qa; TV2: `test_gather_l2.py::Harvest` | [gather.jsonl](../proof/phase-1/gather.jsonl) tick 151, 801 | ⏳ (TV2 báo đạt) |
| AC-P1-15 | Nút từ 1 về 0 → `node_regrown` theo id, hái được ngay | qa; TV2: `Harvest.test_moc_lai_roi_hai_duoc_ngay` | `test-run.txt` | ⏳ (TV2 báo đạt) |
| AC-P1-16 | `catch` chỉ khi hết hồi và dưới nước: đàn gần nhất trong 2.0 m, hòa theo id; thêm đủ yield (ca_linh 3, ca_loc 1), xóa đàn, `fish_caught`, hồi 30 tick; thiếu chỗ → `hold_full`, giữ đàn, không hồi chiêu; không có đàn → không event | qa; TV2: `test_gather_l2.py::Catch` | [gather.jsonl](../proof/phase-1/gather.jsonl) tick 263, 596 | ⏳ (TV2 báo đạt) |
| AC-P1-17 | Hết giờ → `gather_end` `time` ở mọi độ sâu, giữ giỏ; hái/bắt/cập bến ở bước cuối vẫn tính | smoke: `test_time_ends_gather_and_keeps_hold`; qa: hành động ở bước cuối | `test-run.txt` | ⏳ |
| AC-P1-18 | File kho: chỉ khóa `items`, bỏ lượng 0, khớp `gather_end.inventory`; ghi đúng một lần (ngất ghi rỗng); chạm `--ticks` trước thì không ghi; ghi nguyên tử | smoke: `test_inv_01_not_written_when_tick_limit_first`; qa: ngất → `{"items":{}}` | `catch.json` | ⏳ |

## Quán — lát 3: khách, giữ chỗ, kiên nhẫn (TV3)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-19 | Quán đọc kho: sai schema, kind lạ → mã 2; thiếu kho thì rỗng; tiền, earned đầu lượt = 0; uy tín theo tuning | smoke: `test_inv_bad_schema_exit_2`, `test_inventory_and_scenario_stock_conflict` | `test-run.txt` | ⏳ |
| AC-P1-20 | Khách đến ở `phase_tick` 120 rồi mỗi 900 tick; lấy bàn trống id nhỏ nhất; hết bàn thì bỏ lượt; không món đủ → `no_dish` | qa | `test-run.txt` | ⏳ |
| AC-P1-21 | Chọn đều theo seed trong các món đủ nguyên liệu khả dụng (tồn − giữ); giữ đúng công thức ngay; `customer_arrived`; hai khách tranh phần cuối được xử lý đúng | qa (fixture `random_customers:false`) | `test-run.txt` | ⏳ |
| AC-P1-22 | Kiên nhẫn giảm từ bước sau khi đến; về 0 khi còn giờ → `customer_left` `patience`, uy tín −0.5 (kẹp 0–5), nhả giữ chỗ, bỏ món của đơn | qa | `test-run.txt` | ⏳ |

## Quán — lát 4: bếp, bưng, phục vụ, tiền (TV4)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-23 | Tối đa một `interact`/bước, chọn theo (khoảng cách, bếp trước bàn, id); đối tượng chọn được nhưng không tương tác được thì bỏ lượt | qa | `test-run.txt` | ⏳ |
| AC-P1-24 | Bếp idle lấy đơn reserved cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, `cook_started` (items sắp theo kind, base_price); nấu xong → ready, `dish_ready` | qa | `test-run.txt` | ⏳ |
| AC-P1-25 | Bếp ready + tay trống → `dish_picked`, bếp về idle; `carry_limit` 1 | qa | `test-run.txt` | ⏳ |
| AC-P1-26 | Phục vụ đúng `order_id` → `served`, khách ăn 600 tick; boa = floor(giá × 0.2) nếu tỷ lệ kiên nhẫn ≥ 0.5, ngược lại 0 | qa | `test-run.txt` | ⏳ |
| AC-P1-27 | Ăn xong → `paid` `finished_eating`, rời bàn; boa dương +0.2 uy tín (kẹp) | qa | `test-run.txt` | ⏳ |
| AC-P1-28 | Hết ca: khách đang ăn trả `closing`, khách chờ rời `closing` không trừ uy tín; `quan_end` đủ money/earned/shift_earned/reputation | qa | `quan-seed1.jsonl` | ⏳ |

## Tích hợp & DoD (mục 7)

| AC | Yêu cầu (PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-29 | Smoke hai tiến trình: `dock.json` + `dock-inputs.json` → quán tick 0 có `stock:{"bong_sung":2,"ca_loc":1}` | smoke: `test_inv_01_gather_writes_inventory_quan_reads_it` + chạy tay 2 lệnh mục G; TV2: `tools/check_handoff.py` | [handoff.txt](../proof/phase-1/handoff.txt) | ⏳ (TV2 báo đạt, khớp 6 món) |
| AC-P1-30 | Chơi được cả hai buổi; HUD hiện thời gian, oxy, Máu, giỏ (sáng) và kho, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín (tối) | chơi thử `python3 -m chonoi.live`, chụp màn hình | `docs/proof/phase-1/hud-*.png` | ⏳ |
| AC-P1-31 | README: chạy từ clone sạch ≤ 3 lệnh, điều khiển, cách tính điểm, lệnh test 1 lệnh | đọc tay README trên clone sạch | — | ⏳ |
| AC-P1-32 | TEAM.md đủ người + thỏa thuận; `team_size` khớp; hợp đồng kho có schema + ví dụ ở `docs/contracts/` | `tools/check_team.py`, đọc tay | `check-team.txt` | ⏳ |
| AC-P1-33 | Ghi chép tối thiểu: `clarify.md`, `ai-usage-log.md`, verification + proof | đọc tay | — | ⏳ |
| AC-P1-34 | Tag `phase-1` trỏ commit bàn giao trên `main`, trước 1:00 | `git show phase-1` | — | ⏳ |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:

## Bảng theo dõi TV1 trước khi đồng bộ main

Tham chiếu theo mục của PRD-0 do Sang cung cấp. Kết quả local ghi riêng. Khi bàn giao, TV6 ghi SHA trên main, chạy lại, dẫn log/ảnh đúng bản rồi chốt đạt hoặc chưa đạt từng dòng.

| Yêu cầu PRD-0 | Người | Cách kiểm và bằng chứng | Trạng thái |
|---|---|---|---|
| A–C · preset, CLI, input | TV6 | Đối chiếu preset v1.0, 60 Hz, seed có dấu, tín hiệu cạnh lên và mã thoát 0/1/2. Kiểm input sai trước khi tạo output. | Chờ kiểm bản bàn giao |
| D · fixture | TV3/4/6 | Dựng đơn đúng/sai cho từng trạng thái. Thử giữ quá tồn, khách trùng bàn, bếp và tay cùng giữ một đơn, timer mâu thuẫn, ID tham chiếu thiếu và trường ngoài v1.0. | Chờ kiểm |
| E · JSONL, điểm và tính tất định | TV6 | Kiểm tick 0, event trước snapshot, snapshot cuối duy nhất, lý do gameplay ưu tiên tick_limit. So hai lượt cùng input/seed từng byte cho cả JSONL và kho. Kiểm điểm = earned + 100 × floor(reputation). | Chờ kiểm |
| F · bơi, biên, oxy và giỏ | TV1 | Test di chuyển trong `test_smoke_p1`; [5 test sinh tồn](../../tests/test_gather_survival.py) kiểm biên mặt nước, nhịp ngạt, hồi oxy và thứ tự mất giỏ. [Kho rỗng khi ngất](../proof/phase-1/handoff-tv1-fainted.txt) | Đạt trên nhánh TV1, chờ kiểm lại trên commit bàn giao |
| F · hái, bắt và cập bến | TV2 | Kiểm mép bán kính, hòa theo ID, nút vừa mọc, cả đàn vượt sức chứa, hồi chiêu, cập bến/hái/bắt ở bước cuối. | Chờ hoàn thiện luật và kiểm |
| F · khách, bàn và kho khả dụng | TV3 | Kiểm lịch khách theo phase_tick, kể cả khi rút ngắn ca. Bàn bận bỏ lượt, bàn trống thiếu món phát no_dish. Kiểm giữ/nhả, thu hồi món của đơn hết hạn và uy tín. | Chờ hoàn thiện luật và kiểm |
| F · bếp, bàn, thu tiền | TV4 | Kiểm một interact, bếp trước bàn khi hòa, bỏ lượt nếu đối tượng gần nhất chưa dùng được. Phục vụ ở tick hết kiên nhẫn/hết ca, chốt boa lúc giao và cộng uy tín lúc thu. | Chờ hoàn thiện luật và kiểm |
| G · smoke hai tiến trình | TV2/6 | Đã chạy hai lệnh mục G với seed 42 trên workspace (HEAD `f0a1906`, có thay đổi local). Cập bến tick 1. Inventory trong gather_end, file kho và stock quán tick 0 đều có 2 bong_sung, 1 ca_loc. Khi chạy trên main, lưu log theo §6.3. | Đạt trên workspace, chờ chạy lại trên commit bàn giao |
| G · các nhánh file kho | TV2/6 | Kiểm ngất ghi rỗng, hết giờ giữ giỏ, tick_limit giữ nguyên file có sẵn, ghi nguyên tử. Kiểm quán độc lập kho rỗng, kho quán vượt trần giỏ vẫn hợp lệ. | Chờ kiểm |
| §2–3, §7 · chơi và HUD | TV5/6 | Chơi cả hai ca, nấu từ kho vừa thu, chụp hai màn hình đủ trường HUD theo kế hoạch. Kiểm góc nhìn và nguồn asset. | Chờ chơi thử trên main |
| §6–7 · tài liệu và bàn giao | TV1/3/5/6 | Từ clone sạch chạy README, kiểm schema + ví dụ kho, roster/quyền Write, nhật ký và bằng chứng ở SHA đã kiểm. Xác nhận tag remote trỏ đúng SHA. | Chờ bàn giao |

### Ghi chú lần kiểm local

Smoke G hiện dùng giỏ dựng sẵn. Ca này chứng minh đường truyền kho. Các lát thu hoạch, sinh tồn, phục vụ và HUD cần bằng chứng riêng. Sau khi chạy trên main, ghi các AC còn thiếu và hành động cho phase sau tại đây.
