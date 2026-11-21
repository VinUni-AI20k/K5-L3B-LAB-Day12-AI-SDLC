# Phase 1 — Đối chiếu PRD-0 (bản thật) với starter

> Nguồn: PRD-0 Phase 1 do nhóm dán ngày 2026-11-21 (bản trên lab board `#phase-1`). Bản này **không có trong repo** —
> đừng sửa, chỉ đọc. Mọi con số vẫn lấy từ `game.contract.json`.
> Ký hiệu: ✅ starter đã đúng · 🟡 đúng một phần · ❌ chưa có.

## 0. Ba câu chốt

1. Phase 1 = **cả hai buổi**. Buổi sáng (gather) đầy đủ + buổi tối (quan) đầy đủ. Không phải "P1 chỉ gather".
2. Bốn lát ở PRD §6.2 **trùng đúng bốn `TODO(nhóm)`** trong starter: `gather.py` lát 1–2, `quan.py` lát 3–4.
3. Event payload đã cố định **từng khóa** ở §E. Sai tên khóa / thừa khóa là mất điểm dù luật đúng.

## 1. Những chỗ hiểu sai trước đây (đã sửa)

| Chỗ | Đoán trước | PRD thật |
|---|---|---|
| Bắt cá | giữ đàn, chỉ hồi chiêu | **xóa đàn**, mỗi lần bắt lấy hết `yield` |
| Hồi chiêu khi giỏ đầy | không hồi chiêu | "giữ đàn và cooldown" — ❓ còn mơ hồ, xem §5 Q1 |
| Ngạt | 60 tick sau khi oxy về 0 | lần đầu ở **t+59** nếu đếm ban đầu 0 |
| `hold_full` | `{capacity}` | `{action, node_id hoặc fish_id, required, free}` |
| `faint` | `{}` | `{cause:"choke", lost, hp:0}`, `lost` là mảng kind theo thứ tự bỏ **LIFO** |
| Phạm vi P1 | gather | **gather + quan** |
| Quán: chọn đối tượng | thử lần lượt đến khi được | chọn **một** theo (khoảng cách, bếp trước bàn, id); không tương tác được thì **bỏ lượt** |
| Boa | theo kiên nhẫn còn lại | `floor(base_price × tip_rate)` nếu **tỷ lệ kiên nhẫn sau bước 1** ≥ `tip_min_patience_ratio` |
| `phase_tick` | bằng `tick` | bắt đầu 0, tăng mỗi bước, **dùng sau tăng** cho lịch khách; lịch vẫn tính từ 0 khi rút ngắn ca |

## 2. Bốn lát → file → test → người (nhóm 5)

| Lát (PRD §6.2) | Nội dung | File | Test bắt buộc | Người |
|---|---|---|---|---|
| 1 | Bơi, oxy, chặn biên, giỏ | `chonoi/sim/gather.py` (bước 4–7) | 6 ca: oxy mặt/dưới, `oxygen_empty`, `choke` t+59, `faint` xóa giỏ, biên | Cao Minh |
| 2 | Hái, bắt cá, cập bến, ghi kho | `chonoi/sim/gather_actions.py` | 6 ca: hái gần nhất + hòa id, `hold_full`, regrow 1200, bắt xóa đàn, hồi chiêu, dock trước hái | Nhật Minh |
| 3 | Khách, giữ chỗ, kiên nhẫn | `chonoi/sim/quan_customers.py` | 5 ca: đến đúng tick, giữ đúng công thức, hết kiên nhẫn, `no_dish`, nhả giữ chỗ | Nhật Minh |
| 4 | Bếp, bưng, phục vụ, tiền | `chonoi/sim/quan_service.py` | 6 ca: nấu trừ kho, `ready_ticks`, bưng 1 món, phục vụ đúng order, boa, đóng ca | Cao Minh |
| — | HUD cả hai buổi | `chonoi/web/index.html` | chơi thử bằng mắt + ảnh | Vinh |
| — | QA/ma trận/bằng chứng | `tests/`, `docs/verification/` | chạy 1 lệnh | Văn Minh |
| — | TEAM/contract/skill/tag | `TEAM.md`, `AGENTS.md`, `.agents/skills/` | `tools/check_team.py` | Đức Minh |

Vì sao tách `gather_actions.py` / `quan_customers.py` / `quan_service.py`: bốn lát chạy **song song** trong 60 phút,
mỗi người một file thì không conflict. `GatherSim.step()` và `QuanSim.step()` chỉ gọi helper, phần sửa trong file chính là của
Cao Minh (gather) / Nhật Minh (quan) để tránh hai người cùng sửa một hàm.

## 3. Checklist theo mục PRD

### A. `game.contract.json`

- ✅ đủ khóa, đúng preset.
- ❌ `"team": "ten-nhom"` → `"MMMMV"`; `"team_size": 4` → `5`.
- ✅ `build_cmd`/`run_cmd`/`headless_cmd` khớp Python.

### B. Cờ headless

- ✅ `--mode/--seed/--ticks/--out/--scenario/--inputs/--inventory/--inventory-out/--snapshot-every`.
- ✅ `--ticks` âm → 2; `--snapshot-every <= 0` → 2; `--inventory` chỉ với `quan`; `--inventory-out` chỉ với `gather`;
  đường dẫn trùng nhau → 2; kiểm **trước** khi ghi đầu ra.
- ✅ `--mode day` bị từ chối mã 2 (contract v1.0 chỉ có gather|quan).
- 🟡 "Gameplay kết thúc thì dừng sớm, ghi snapshot cuối và end" — `runner.run` đã làm; cần test tick dừng không phải bội số.

### C. Inputs

- ✅ tick tăng nghiêm ngặt, tick lặp/giảm → 2; `move` hữu hạn trong [−1,1]; chuẩn hóa >1; trường lạ → 2.
- ✅ nút chỉ tác động ở **cạnh lên**; thiếu frame thì giữ `move` cũ, nút cũ.
- ✅ "hành động đúng kiểu nhưng sai pha được bỏ qua" — ví dụ `catch` trong `quan` hiện không được đọc; giữ nguyên.

### D. Scenario — **thiếu nhiều**

| Trường | PRD | Starter | Việc |
|---|---|---|---|
| `gather.player` | 7 khóa: pos, vel, heading_deg, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks | nhận thêm `invuln_ticks` | ❌ bỏ `invuln_ticks` (PRD không có → phải mã 2); bỏ khỏi snapshot nếu muốn khớp tuyệt đối |
| `quan.hand` | payload `{order_id,dish_id,base_price}` hoặc null | nhận gì cũng được | ❌ kiểm schema |
| `quan.stoves[]` | `{id,pos,state,cook_ticks_left,ready_ticks}`; `ready_ticks` = tuổi món | merge thô | ❌ kiểm state ∈ idle/cooking/ready; cooking phải có timer dương + món khớp đơn |
| `quan.customers[]` | `{id,table_id,dish_id,order_tick,state,patience_ticks_left,eat_ticks_left,order_status,reserved,base_price,tip}` | chỉ id + table_id | ❌ kiểm đủ: state ∈ waiting/eating; order_status ∈ reserved/assigned/unfulfillable/served; ăn phải served + timer ăn dương + base_price,tip; assigned đúng 1 món ở bếp/tay, reserved rỗng; reserved khớp công thức và ≤ tồn |
| `quan.stock` | gồm cả phần giữ chỗ | ✅ đọc được | ❌ kiểm `reserved` không vượt tồn |
| `gather.nodes/fish` | ✅ | ✅ | — |
| `random_*` | mặc định true | 🟡 `random_fish` có, `random_customers` chưa dùng | ❌ cài `random_customers:false` tắt sinh khách |

### E. Output JSONL

- 🟡 `snapshot` chung: `tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score` ✅.
- 🟡 `gather`: `player` (bỏ `invuln_ticks`), `oxygen_max_ticks, hp_max, at_surface`, `hold, hold_count, hold_capacity, nodes[], fish[]` ✅.
- ❌ `quan`: `tables[]` phải có `customer_id` (null khi trống); **chỉ liệt kê khách còn ngồi**; `customers[]` đúng schema D.
- ❌ Event payload — xem §4. Starter mới có `node_regrown` + `gather_end`; 6 event gather + 9 event quán còn thiếu.
- ✅ `end` đủ khóa; `score = earned + 100*floor(reputation)`.
- ✅ làm tròn 3 chữ số, sắp id bằng `id_key`, hold theo thứ tự nhặt.
- 🟡 "Kết thúc đúng bước cuối được cấp thì ưu tiên lý do gameplay" — kiểm bằng test tick cuối.

### F. Luật một bước

Chung: mỗi bước `sim_tick += 1`, `phase_tick += 1`; timer không âm; cooldown `L` đặt ở `t` dùng lại từ `t+L`;
thực thể sinh cuối bước chỉ tham gia từ bước sau; Euclid trên mặt phẳng pha, tính cả mép bán kính; vận tốc hội tụ trong
`ramp_max_ticks` rồi giữ đích; chặn biên và triệt vận tốc hướng ra.

**Gather** — thứ tự đúng như PRD (khớp khung starter):

1. ⏱ giảm `time_left_ticks`, `catch_cd_ticks`; nút `1→0` phát `node_regrown`, hái được ngay bước đó.
2. 🏊 bơi + chặn biên.
3. 🌊 so `at_surface()` đầu/cuối bước → `dive`/`surface` (`pos` sau di chuyển, chỉ khi đổi phía).
4. 🫧 oxy theo `d` **cuối bước**: mặt (`d ≤ 0.5`) +6 kẹp max, reset ngạt; dưới nước −1 kẹp 0; `oxygen_empty` khi từ >0 xuống 0.
5. 😮 dưới nước kết thúc bước với oxy 0 (kể cả bước vừa chạm 0) → `zero_oxy_ticks += 1`; đủ 60 → đặt lại 0, `hp -= 1`, `choke`
   (`hp` sau trừ). `hp == 0` → bỏ giỏ **LIFO**, `faint {cause:"choke", lost, hp:0}` rồi `gather_end` `fainted` + kho rỗng, dừng bước.
6. ⚓ `interact`: trong `dock_radius` → `gather_end` `docked` ngay. Ngoài bến **chỉ khi ở mặt nước**: nút `ready` gần nhất trong
   `interact_radius`, hòa theo id; đủ chỗ → +1 `node_yield`, `regrow_ticks = regrow_s*60`, `gather`; thiếu chỗ → `hold_full`, nút giữ nguyên.
7. 🎣 `catch`: hết hồi + **dưới nước** → đàn gần nhất trong `catch_radius`, hòa theo id; đủ chỗ → +toàn bộ `yield`, **xóa đàn**,
   `fish_caught`, đặt hồi chiêu; thiếu chỗ → `hold_full`, không thử đàn khác; không có đàn → không event, không hồi chiêu.
8. ⌛ `time_left_ticks == 0` → kết thúc `time` ở mọi độ sâu, giữ giỏ sau các hành động trên, chốt kho ngay.

**Quán** — thứ tự PRD:

1. ⏱ giảm `time_left_ticks`, timer nấu/ăn/kiên nhẫn. `ready_ticks` chỉ tăng cho món **đã ready ở đầu bước**.
2. 🍳 theo id bếp: nấu xong → `ready`, `ready_ticks = 0`. `burn_s = null` (không cháy).
3. 🚶 di chuyển.
4. 🖐 **tối đa một** `interact`: chọn theo (khoảng cách, bếp trước bàn, id). Đối tượng chọn được mà không tương tác được → **bỏ lượt**.
   - bếp `idle` → lấy đơn `reserved` **cũ nhất** (`order_tick`, rồi id bàn), tiêu đúng phần giữ, chốt `base_price`, bắt đầu nấu (`cook_started`);
   - bếp `ready` → giao món vào tay trống, bếp về `idle` (`dish_picked`);
   - bàn có khách đúng `order_id` → khách ăn, timer ăn đầy (`served`), chốt boa theo `tip_rate` nếu tỷ lệ kiên nhẫn sau bước 1 ≥ ngưỡng.
5. 🍽 theo id bàn: khách ăn xong → trả tiền rồi rời ngay (`paid` `finished_eating`).
6. 🚪 còn giờ: khách `waiting` có kiên nhẫn 0 → rời (`customer_left` `patience`), uy tín `+left_reputation_delta`.
7. 🌙 hết ca: khách đang ăn trả ngay (kể cả vừa được giao món), khách còn chờ rời với `closing` **không trừ uy tín**; dọn xong phát `quan_end`.
8. 👥 còn giờ: xét lượt khách theo `first_customer_tick`, rồi mỗi `customer_interval_s*60`; hết bàn → bỏ lượt; bàn trống id nhỏ nhất;
   chọn **đều theo seed** trong 3 món đủ nguyên liệu khả dụng (tồn − giữ); không món nào → `no_dish`; khách mới giữ đúng công thức ngay,
   `order_tick = phase_tick` hiện tại, kiên nhẫn đầy, giảm từ bước sau.

Khi khách rời: nhả phần giữ thô, bỏ món của đơn đang nấu/ready/trên tay; nguyên liệu đã dùng **không hoàn**.

### G. File kho

- ✅ schema, atomic write, bỏ khóa 0, từ chối kind lạ/số âm.
- ✅ chỉ ghi khi `gather_end`; ngất ghi `{"items":{}}`; `--ticks` chạm trước khi kết thúc → không tạo/ghi đè.
- ✅ quán không có `--inventory` và không có `stock` → kho rỗng.

## 4. Event — payload chính xác (§E)

| Name | Data |
|---|---|
| `gather` | `node_id, kind, amount` |
| `node_regrown` | `node_id` |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` |
| `fish_caught` | `fish_id, kind, yield` (một event mỗi đàn, lấy đủ yield) |
| `dive` / `surface` | `pos` |
| `oxygen_empty` | `oxygen_ticks: 0` |
| `choke` | `hp` (sau trừ) |
| `faint` | `cause:"choke"`, `lost` (mảng kind, thứ tự bỏ LIFO), `hp: 0` |
| `gather_end` | `reason`, `inventory` (object) |
| `customer_arrived` | `order_id, table_id, dish_id` |
| `no_dish` | `{}` (có bàn nhưng thiếu món) |
| `cook_started` | `stove_id, order_id, dish_id, items, base_price` |
| `dish_ready` | `stove_id, order_id, dish_id` |
| `dish_picked` | `stove_id, order_id, dish_id` |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (`finished_eating`/`closing`) |
| `customer_left` | `order_id, table_id, reason` (`patience`/`closing`), `reputation` |
| `quan_end` | `reason:"time", money, earned, shift_earned, reputation` |

## 5. Câu hỏi cho Anh Năm (dán vào `docs/clarify.md`)

| # | Câu hỏi | Giả định tạm |
|---|---|---|
| Q1 | `catch` khi giỏ không đủ chỗ: có đặt hồi chiêu không? (PRD: "giữ đàn và cooldown") | Không đặt hồi chiêu — "cooldown" ở đây là giữ nguyên bộ đếm cũ |
| Q2 | `paid.amount` = `base_price + tip`? | Đúng |
| Q3 | `cook_started.items` là mảng kind đã tiêu, có lặp lại (vd `["bong_sung","bong_sung"]`)? | Có lặp, sắp theo kind |
| Q4 | `gather.amount` luôn bằng `node_yield` (=1)? | Đúng |
| Q5 | `faint.lost` khi giỏ rỗng là `[]`? | Đúng |
| Q6 | Khách ăn xong và khách mới đến cùng một tick: thứ tự event? | Trả tiền/rời trước, sinh khách sau |
| Q7 | `phase_tick` khi `time_left_ticks` bị rút ngắn: vẫn bắt đầu 0? | Đúng |
| Q8 | `invuln_ticks` (starter có, PRD không) — bỏ khỏi scenario/snapshot? | Bỏ |

## 6. Test phải có trước khi tag `phase-1`

1. Oxy mặt nước không giảm; dưới nước 1800 tick → `oxygen_empty` đúng tick.
2. `choke` đầu tiên ở **t+59**; `hp` 3→2→1→0; `faint` có `lost` đúng LIFO; kho rỗng.
3. Hái nút: gần nhất, hòa theo `id_key` (`N2` trước `N10`), nút `regrow>0` bị bỏ qua, `hold_full` không đặt regrow.
4. `regrow_ticks = 1200`, `node_regrown` đúng tick.
5. Bắt cá: xóa đàn, `yield` đúng loài, hồi chiêu 30 tick, không có đàn → không event/không hồi chiêu.
6. Cập bến thắng hái, kể cả khi đứng ở `d = 2.9`.
7. Hết giờ khi đang lặn sâu: vẫn giữ giỏ và ghi kho.
8. Quán: khách đến tick 120, 1020, …; giữ đúng công thức; `no_dish` khi hết nguyên liệu; hết kiên nhẫn → `customer_left` + uy tín −0.5.
9. Nấu trừ kho khi bắt đầu; `ready_ticks` tăng sau khi ready; bưng đúng 1 món; phục vụ sai món bị bỏ lượt.
10. Boa đúng ngưỡng (kiểm cả hai phía `0.5`), uy tín cộng `tip_reputation`, kẹp [0,5].
11. Đóng ca: khách đang ăn trả tiền, khách chờ rời `closing` không trừ uy tín, `quan_end` một lần.
12. Smoke §G: `gather` 1 tick ở bến → `quan` tick 0 có `stock {"bong_sung":2,"ca_loc":1}`.
13. Hai lần chạy cùng seed → JSONL giống từng byte; tick dừng không phải bội số vẫn có snapshot cuối.

## 7. Việc làm ngay

1. Sửa `game.contract.json`: `team`, `team_size`.
2. Bỏ `invuln_ticks` khỏi `scenario.py` + snapshot (hoặc hỏi Anh Năm nếu muốn giữ).
3. Cài 6 event gather + luật lát 1–2.
4. Mở rộng `scenario.py` cho `hand`, `stoves`, `customers` (mã 2 đúng PRD D).
5. Cài `quan_customers.py` + `quan_service.py`, nối `QuanSim.step()`.
6. Viết 13 test ở §6 **trước** khi code để đỏ rồi xanh.
