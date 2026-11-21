# PHASE 2 — IMPLEMENTATION SPECIFICATION
## Quán Ăn Chợ Nổi · TICKET-02 · Test Contract v1.1

> **Mục đích:** Tài liệu đặc tả để toàn nhóm và AI coding agent (Codex/Gemini/Claude) triển khai Phase 2 nhất quán. Đây là bản *tổ chức lại* yêu cầu từ TICKET-02 và phần được kế thừa từ PRD-0/Test Contract v1.0; **không phải một Test Contract mới**.
>
> **Nguồn chuẩn:** (1) TICKET-02 / Test Contract v1.1 do lớp phát hành; (2) PRD-0 / Test Contract v1.0 cho các quy tắc không bị v1.1 thay thế. Nếu bản tài liệu này mâu thuẫn với nguồn chuẩn thì **nguồn chuẩn được ưu tiên**. Tệp `TICKET-02_original.md` và `PRD-0_original.md` trong gói đính kèm lưu nguyên văn để đối chiếu.
>
> **Repo nhóm:** https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini  
> **Thời lượng:** 55 phút (mốc 1:00–1:55); tag bàn giao `phase-2` trên nhánh `main`.  
> **Nhóm:** 5 thành viên. **Công nghệ:** tận dụng Python simulation/headless và web local đang có; không tự ý đổi engine.

---

## 0. Quy tắc bắt buộc dành cho AI coding agent

1. Đọc các file nguồn chuẩn, `game.contract.json`, `README.md`, `AGENTS.md` (nếu có), module cần sửa, tests và `git status` **trước khi code**.
2. So sánh working tree với spec này: chỉ làm phần còn thiếu/chưa đúng, không viết lại tính năng đang chạy đúng, không ghi đè công việc của người khác.
3. Thay giá trị Phase 1 khi v1.1 đã chốt số mới. Những phần chưa được Ticket-02 đổi **phải giữ nguyên quy tắc v1.0**, nhất là tick, input, JSONL, event, inventory và thứ tự xử lý Quán.
4. Mọi hành vi phải kiểm được trên headless, deterministic theo cùng seed và input. UI chỉ hiển thị và gửi điều khiển đến simulation; không viết logic game song song ở browser.
5. Mục nào chưa có quy định đủ rõ: dùng fixture để kiểm thử phần chắc chắn, ghi câu hỏi/giả định vào `docs/clarify.md`, **không biến phỏng đoán thành luật chính thức**.
6. Không âm thầm thêm extension `weapon/net/snake/burn/vendor/ca_ho` khi nhóm chưa chọn. Đừng để bất kỳ extension nào làm sai output lõi.
7. Không reset hard, force-push, tự merge `main` hay gắn tag nếu chưa được nhóm giao. Tự test, ghi bằng chứng thật; không tuyên bố PASS khi chưa chạy.

## 1. Phạm vi và điều kiện hoàn thành

**Mục tiêu người dùng:** chơi trọn tối đa 5 ngày: xem mục tiêu nguyên liệu → lặn/hái → mở quán bán món từ kho thật → tổng kết → mua nâng cấp → ngày tiếp theo. Đầu ngày, Má Tư công bố thực đơn; cuối ngày mở Shop.

**Lõi bắt buộc của Phase 2:**

- `contract_version: "1.1"`, manifest số liệu chuẩn, 6 nguyên liệu và 6 món.
- Gather: cá bơi/sinh (3 loài, 8 đàn đầu ca), 6 nút cây, cá sấu gây sát thương, ngất, giỏ và kho đúng luật.
- Quán: 2 bếp, 4 bàn, 6 món, nhiều khách đồng thời, phục vụ và doanh thu/uy tín chính xác.
- `--mode day`, kế hoạch D1–D5, Shop oxygen/hp, `pause`, state xuyên ngày, các phase/event/snapshot theo v1.1.
- Web local: Menu, DayIntro, EveningIntro, DayResult, Shop, Summary, HUD, pause.
- Test hợp đồng và smoke hai tiến trình + `day --days 1`/nhiều ngày; tài liệu/bằng chứng, retro; tag `phase-2`.

**Mở rộng:** Nhóm 5 người cần ít nhất **1 mục mở rộng trong toàn bộ lab** (không nhất thiết Phase 2), chỉ khi lõi đã ổn định. Mục bật phải khai trong `extensions` của manifest nếu có mã tương ứng.

## 2. Quy ước và phần giữ nguyên từ Test Contract v1.0

- Mô phỏng **60 tick/s**, vị trí đơn vị mét. Gather dùng `[x,d]`, `d` tăng hướng xuống; Quán dùng `[x,z]`, `z` tăng hướng bắc.
- `--ticks` là số bước **ngoài** tối đa, không âm; `--ticks 0` chỉ dựng fixture. `--snapshot-every` nguyên dương, mặc định 10. Bắt buộc `--mode`, `--seed`, `--ticks`, `--out`.
- Input frames tăng tick nghiêm ngặt, không trùng. `move` có hai phần tử hữu hạn trong [-1,1]; nút boolean chỉ tác động ở **cạnh lên**. Không nhận trường không hỗ trợ, kiểu sai, scenario mâu thuẫn.
- Bước gameplay đọc frame ở tick ngoài `k`, cập nhật trạng thái và phát event ở tick `k+1`; `phase_tick` và `sim_tick` chỉ tăng khi thực chạy simulation (không tăng khi pause). Entity sinh cuối bước không hoạt động trước bước tiếp.
- Kho xuất/nhập dùng đúng `{ "items": {"ca_loc":1,"bong_sung":2} }`. Khóa thiếu là 0; không ghi lượng 0. Chỉ ghi inventory-out khi Gather kết thúc; ghi nguyên tử; ngất → kho rỗng. Quán độc lập không có inventory/scenario.stock thì kho rỗng.
- JSONL mỗi dòng 1 object UTF-8; snapshot ở tick 0, bội số của snapshot-every và tick dừng; events trước snapshot; một snapshot tối đa mỗi tick; dòng `end` cuối. Trạng thái/bộ đếm/event phải tuân thủ định dạng v1.0 khi không bị v1.1 sửa.
- Tiền nguyên **nghìn đồng**. `score = earned + 100 × floor(reputation)`; số tiền và event tick phải đúng chính xác. Sắp entity theo ID quy tắc v1.0 (vd F2 trước F10); giữ thứ tự LIFO của giỏ khi rơi đồ.
- Kết quả phải **giống nhau từng byte** với cùng bản chạy/máy/seed/tham số/input; tách đồng hồ render và random UI khỏi simulation.
- Mã thoát: `0` kết thúc hợp lệ/chạm giới hạn; `2` sai cờ/dữ liệu/fixture; `1` runtime/ghi output lỗi. Kiểm tra lỗi đầu vào trước khi ghi đầu ra.

**Chú ý:** Đây là tóm tắt kế thừa; xử lý đầy đủ các tình huống scenario, bộ đếm, validation, tương tác/cạnh, timer và event theo `PRD-0_original.md`, các mục B–G.

## 3. Dữ liệu và số liệu chuẩn Gather

| Thuộc tính | Giá trị bắt buộc |
|---|---|
| Thời lượng | 180s = 10.800 tick |
| Bounds | x ∈ [0,100], d ∈ [0,30] |
| Mặt nước; vùng sâu | surface d ≤ 0.5; nông d < 10; giữa 10 ≤ d < 20; sâu d ≥ 20 |
| Spawn/bến | start [2,0], heading 0°; dock [2,0], radius 3m |
| Bơi | 4.0 m/s; ramp tối đa 6 tick; chặn mép |
| Oxy cơ sở | 30s = 1.800 tick; dưới nước -1/tick, mặt nước +6/tick |
| Ngạt | Ở dưới nước với oxy=0: -1 Máu/60 tick (kể bước chạm 0), reset nhịp khi hồi oxy/lên mặt nước; ngạt xuyên bất tử và **không làm rơi hàng riêng** |
| Máu cơ sở | 3, hồi đầy đầu mỗi ngày; 0 → faint, rơi giỏ còn lại |
| Giỏ | 12 ô; 1 nguyên liệu/ô; khi cá bắt phải đủ chỗ cho nguyên đàn |
| Hái | radius 2m ở mặt nước; +1 cây; mọc lại 1.200 tick; xét dock trước |
| Catch | radius 2m dưới nước; cooldown 30 tick từ lần bắt thành công |
| Fish yield | ca_linh: 3; ca_loc: 1; ca_keo: 2 |
| Hết ca | docked/time giữ hàng; fainted → kho rỗng; trong day vẫn mở Quán |

**Các nút cây cố định (6):**

| ID | Kind | Vị trí `[x,d]` |
|---|---|---|
| N1 | bong_dien_dien | [12,0] |
| N2 | bong_dien_dien | [28,0] |
| N3 | bong_sung | [44,0] |
| N4 | bong_sung | [60,0] |
| N5 | keo_neo | [76,0] |
| N6 | keo_neo | [90,0] |

**Sáu loại nguyên liệu hợp lệ:** `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`. Không tự thêm loại vào lõi/headless.

### 3.1 Cá bơi và sinh đàn

- 3 loài: **cá linh** `ca_linh`, **cá lóc** `ca_loc`, **cá kèo** `ca_keo`.
- Tốc độ bơi 1.5 m/s, hoành độ x nằm trong [4,96]. Dải độ sâu:
  - `ca_linh`: d ∈ [3,12]
  - `ca_loc`: d ∈ [8,20]
  - `ca_keo`: d ∈ [22,28]
- Ở bước bơi thứ 120, 240, ... đổi hướng theo seed **trước** khi bơi; gặp biên thì phản xạ **quãng đường còn lại**, đảo thành phần hướng vuông góc biên; gặp góc đảo cả hai.
- Điểm sinh: x ∈ {15,30,45,60,75,90}; cá linh có d ∈ {5,10}, cá lóc {10,16}, cá kèo {24,27}. Tổng **36 cặp loài-vị trí**, **30 vị trí hình học khác nhau** (hai loài có thể chia sẻ tọa độ tại d=10).
- Đầu ca **8 đàn tại 8 vị trí khác nhau**; tối đa **12 đàn còn sống**.
- Tại `phase_tick = 360*k` (k ≥ 1), **sau khi cá bơi**, tối đa 1 đàn mới nếu dưới trần và tồn tại điểm cách **mọi đàn đang sống > 1m**. Không có điểm → bỏ lượt.
- Chọn loài theo trọng số 0.4/0.3/0.3, chuẩn hóa lại trên loài còn điểm hợp lệ; chọn đều một điểm hợp lệ rồi lấy heading theo seed.
- Cá mới sinh chỉ di chuyển/tương tác từ bước sau. Catch xét **vị trí cá trước khi cá bơi** ở tick đó.
- Scenario `random_fish:false`: tắt đàn cá mặc định, bơi và sinh, cá fixture đứng yên. `gather.fish[]` khi random bật sẽ thay đàn đầu ca nhưng vẫn bơi/sinh; fish có `age_ticks` (mặc định 0).
- Event mới: `fish_spawned` `{id,kind,pos}`. Catch vẫn theo event/giỏ/cooldown v1.0.

### 3.2 Cá Sấu Năm Chèo và sát thương

| Trường | Giá trị |
|---|---|
| Loài | `ca_sau` |
| M1 | Ngày 1+, từ [60,24] ↔ [64,24] |
| M2 | Ngày 3+, từ [85,18] ↔ [89,18] |
| Gather độc lập | Dùng bố trí Ngày 1 |
| Dải độ sâu | d ∈ [10,30] |
| Patrol | 1.0 m/s tới waypoint, đổi mục tiêu từ bước tiếp theo sau khi đến |
| Chase | 3.0 m/s hướng người chơi |
| Detect | người chơi d ≥ 10 và khoảng cách ≤ 10m |
| Exit chase | khoảng cách > 16m hoặc người chơi d < 10 |
| Hit | khoảng cách ≤ 1.5m sau khi cả hai di chuyển; người chơi d ≥ 10; không trong bất tử |
| Thiệt hại | -1 Máu; bỏ `floor(hold_count / 2)` nguyên liệu theo LIFO |
| Bất tử sau hit | 90 tick, trong thời gian đó không hit mới và không kích recoil do va chạm |
| Recoil con gây hit | 60 bước tính từ bước tiếp, đi xa người chơi theo hướng chốt lúc chạm (trùng tâm +x), mỗi bước 2/60m, không gây hit |
| Tối đa hit | 1 hit mỗi bước; chọn quái gần nhất, hòa theo ID |
| HP=0 | Phát `faint` nguyên nhân monster và `gather_end(fainted)` tức thì; Shop/Quán tiếp tục theo Day Loop |

- Quái bị chặn bởi bounds chung và dải độ sâu loài.
- Scenario `gather.monsters[]` **thay danh sách mặc định**, mỗi phần tử nhận `{id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}`; có đúng 2 waypoint, `target_idx` mặc định 1, `state` mặc định `patrol`, `recoil_dir` null trừ recoil; timer recoil/stunned phải dương. Không tự suy diễn state khác ngoài contract/extension đã bật.
- Event `monster_hit`: `{monster_id,hp,lost,pos}`; `lost` theo LIFO; `faint` hỗ trợ cause `monster` và `choke` theo nguồn tương ứng.

### 3.3 Thứ tự xử lý một tick Gather (bắt buộc)

1. Đồng hồ, hồi catch/nút cây và giảm invulnerability.
2. Bơi/chặn biên, oxy, ngạt; nếu Máu về 0 → `faint` rồi `gather_end` và **dừng bước**.
3. Nếu có extension Lao thì xử lý tại vị trí quy định; cập nhật monster theo ID, xét **tối đa một hit**; faint do hit thì kết thúc ngay.
4. Xử lý cạnh `interact`: **dock trước** node hái.
5. Xử lý `catch` theo vị trí đàn **trước khi bơi**, rồi `photo` nếu extension bật.
6. Xét hết giờ (time) sau tương tác/catch.
7. Chỉ nếu còn ca: cá bơi, cá sinh; sau đó Cá Hô nếu extension bật.

**Boundary:** choke có thể đứng trước monster_hit và hết ca trong cùng tick. Cập bến ở tick cuối ưu tiên hơn catch/hết giờ khi còn Máu. Đúng mép bán kính vẫn hợp lệ.

## 4. Dữ liệu và số liệu chuẩn Quán

| Thuộc tính | Giá trị |
|---|---|
| Thời lượng | 180s = 10.800 tick |
| Bounds, spawn | x [0,16], z [0,10]; spawn [8,5] |
| Đi lại | 4.0 m/s, ramp tối đa 6 tick, xuyên nội thất |
| Bếp | B1 [2,8], B2 [5,8] |
| Bàn | T1 [9,2], T2 [13,2], T3 [9,6], T4 [13,6] |
| Interact | radius ≤ 1.5m; gần nhất → ưu tiên bếp trước bàn → ID |
| Tay | Tối đa 1 món |
| Khách tự sinh | tick 120, rồi 120 + 900*k (k≥0); chỉ khi có bàn trống |
| Thời gian | kiên nhẫn 3.600 tick; ăn 600 tick |
| Boa | floor(price × 0.2) khi còn ≥ 50% kiên nhẫn ở tick phục vụ; còn dưới ngưỡng → 0 |
| Uy tín | ban đầu 3.0; kẹp [0,5]; boa dương khi thu tiền +0.2; hết kiên nhẫn giữa ca -0.5 |
| Cháy món | `burn_s: null` trong lõi, không triển khai burn trừ khi chọn extension |
| Điểm | `earned + 100 × floor(reputation)` |

### 4.1 Sáu món và công thức BẮT BUỘC

| ID | Tên | Recipe (kind → số lượng) | Nấu | Giá (nghìn đồng) |
|---|---|---|---:|---:|
| `ca_loc_nuong_trui` | Cá lóc nướng trui | `ca_loc:1` | 6s / 360 tick | 60 |
| `goi_bong_sung` | Gỏi bông súng | `bong_sung:2` | 4s / 240 tick | 40 |
| `lau_ca_linh_dien_dien` | Lẩu cá linh bông điên điển | `ca_linh:3`, `bong_dien_dien:1` | 10s / 600 tick | 120 |
| `canh_chua_ca_loc` | Canh chua cá lóc bông điên điển | `ca_loc:1`, `bong_dien_dien:1` | 8s / 480 tick | 90 |
| `ca_keo_nuong` | Cá kèo nướng muối ớt | `ca_keo:2` | 6s / 360 tick | 70 |
| `lau_mam` | Lẩu mắm miền Tây | `ca_linh:2`, `ca_keo:1`, `keo_neo:1`, `bong_dien_dien:1` | 12s / 720 tick | 200 |

**Nguồn dữ liệu:** recipes/giá/thời gian nấu phải nằm trong manifest/tuning, không hardcode trong gameplay. Mode `quan` độc lập dùng **cả 6 món**; mode `day` giới hạn chọn món theo **ID thuộc kế hoạch ngày** rồi mới lọc đủ nguyên liệu khả dụng.

### 4.2 Đơn hàng, bếp, phục vụ và thanh toán (kế thừa v1.0)

- Khách ngồi bàn trống có ID nhỏ nhất, gọi món trong danh sách được phép và đủ tồn khả dụng (`stock` trừ phần đang giữ), giữ nguyên liệu khi đặt. `order_tick` là phase_tick hiện tại, kiên nhẫn giảm từ **bước sau**.
- Trạng thái đơn: `reserved`, `assigned`, `unfulfillable`, `served`; khách `waiting`, `eating`; `hand` có `{order_id,dish_id,base_price}`.
- Tương tác bếp idle chọn **đơn reserved cũ nhất** theo `(order_tick, table_id)`, tiêu phần giữ, chuyển assigned, chốt giá, phát `cook_started`.
- Hai bếp độc lập. Nấu đủ tick → `ready` (chỉ một `dish_ready`), nhấc món khi tay trống → `dish_picked` và bếp idle.
- Phục vụ bàn phải đúng `order_id` và món, chuyển `eating`, chốt boa ngay lúc phục vụ theo **kiên nhẫn sau bước giảm timer**. Phục vụ khi patience vừa về 0 hoặc đúng tick đóng ca vẫn hợp lệ.
- Khách ăn hết timer: trả `base_price + tip` **một lần**, tăng `money`, `earned`, `shift_earned`; có boa dương thì cộng uy tín (kẹp). Phát `paid` rồi giải phóng bàn.
- Khách hết kiên nhẫn khi chưa hết ca: `customer_left(patience)`, -0.5 uy tín; dọn món đang nấu/ready/trên tay của đơn đó, nhả nguyên liệu **chưa tiêu**; không hoàn trả nguyên liệu đã dùng để nấu.
- Hết ca: khách đang ăn **trả ngay** với `paid(reason=closing)`, kể cả vừa được giao; khách còn chờ `customer_left(reason=closing)` và **không trừ uy tín**; dọn toàn bộ, phát `quan_end(reason=time)`.
- Event kế thừa: `customer_arrived`, `no_dish`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `customer_left`, `quan_end`. Payload chuẩn theo PRD-0 mục E; **không thêm/bỏ field tùy ý**.
- Tick processing Quán **không đổi v1.0**: giảm các timer → xử lý bếp theo ID → di chuyển/chọn một tương tác → xử lý khách ăn xong, hết kiên nhẫn, đóng ca → nếu còn giờ xét sinh khách. Nếu bật burn mới chèn xét cháy đúng vị trí v1.1.

## 5. Day Mode, kế hoạch D1–D5

**Luồng trải nghiệm UI:** `DayIntro → Gather → EveningIntro → Quan → DayResult → Shop → DayIntro` hoặc `Summary` sau ngày cuối.  
**Simulation headless day:** snapshot `phase` chỉ có `gather`, `quan`, `shop`. Các màn DayIntro/EveningIntro/DayResult/Summary là trình bày UI; không tự ý thêm phase headless ngoài contract.

- Khi bắt đầu ngày: công bố `day_plan(dishes, ingredients)`, hồi Máu và oxy theo **active_upgrades**, giỏ trống; giữ `money`, `earned`, `reputation`, upgrades đã mua. Kho dư bị loại sau Shop (trừ extension vendor nếu có logic riêng).
- Ngày hoàn tất **khi Shop đóng**, kể cả ngày 5. Shop có thể đóng sớm. Một ngày không pause tối đa 10.800 Gather + 10.800 Quán + 600 Shop = **22.200 tick gameplay** (các màn UI có thời lượng riêng theo yêu cầu giao diện).
- Số suất kế hoạch là **mục tiêu thu gom**, **không giới hạn số đơn bán**: khách vẫn gọi thêm món đủ nguyên liệu, kể cả đã đạt số suất dự kiến. Không thưởng riêng nếu thu đủ mục tiêu.
- Khách mode `day` chỉ chọn món có ID nằm trong `day_plan.dishes` và đủ nguyên liệu khả dụng. Mode `quan` độc lập cho phép toàn menu.

| Ngày | Món/số suất kế hoạch | Tổng nguyên liệu phải tính theo công thức | Số ô theo Ticket-02 |
|---|---|---|---|
| D1 | `ca_loc_nuong_trui ×3`, `goi_bong_sung ×3` | `ca_loc:3`, `bong_sung:6` | 9 |
| D2 | `ca_loc_nuong_trui ×2`, `lau_ca_linh_dien_dien ×2` | `ca_loc:2`, `ca_linh:6`, `bong_dien_dien:2` | 10 |
| D3 | `goi_bong_sung ×2`, `canh_chua_ca_loc ×2`, `ca_keo_nuong ×2` | `bong_sung:4`, `ca_loc:2`, `bong_dien_dien:2`, `ca_keo:4` | 12 |
| D4 | `lau_mam ×1`, `ca_loc_nuong_trui ×2`, `goi_bong_sung ×1` | `ca_linh:2`, `ca_keo:1`, `keo_neo:1`, `bong_dien_dien:1`, `ca_loc:2`, `bong_sung:2` | 9 (thực tế 11) |
| D5 | `lau_mam ×1`, `lau_ca_linh_dien_dien ×1`, `ca_loc_nuong_trui ×1` | `ca_linh:5`, `ca_keo:1`, `keo_neo:1`, `bong_dien_dien:2`, `ca_loc:1` | 10 (thực tế 12) |

**Lưu ý:** các số `9 (11)` và `10 (12)` là **nguyên văn quy ước từ Ticket-02**: tổng nhu cầu theo công thức vs thực tế bắt theo cả đàn. Không tự sửa biểu thức hoặc đổi dữ liệu kế hoạch.

### 5.1 Shop (core)

| Nâng cấp | Cấp 1 | Cấp 2 |
|---|---|---|
| `oxygen` | Giá 200 → oxy 45s / 2.700 tick | Giá 400 → oxy 60s / 3.600 tick |
| `hp` | Giá 250 → 4 Máu | Giá 500 → 5 Máu |

- Mua **cấp kế tiếp**, từng cấp một. Bằng đúng giá vẫn mua được. Thành công trừ `money`, **không giảm `earned`**, điểm đã tích lũy vẫn theo earned/uy tín.
- `upgrades` phản ánh **cấp đã mua**, `active_upgrades` là **cấp đang có hiệu lực**. Mua hôm nay hiển thị ngay nhưng **chỉ áp dụng từ đầu ngày sau**, khi dựng ngày mới sao cấp đã mua sang active.
- Không đủ tiền, đã cấp tối đa hoặc mã lệnh sai: phát `buy_failed(action,reason)` đúng lý do contract (`funds`, `max_level`, `out_of_stock`, `unknown`), không thay đổi tiền/cấp.
- Shop có `max_ticks:600` **tick hoạt động**. Xử lý một `buy` trước cạnh `shop_done`, kể cả bước cuối. `shop_done` đóng với `shop_end(done)`; tự hết timer phát `shop_end(time)`.
- Khi Shop đóng, tăng `days_completed`; nếu chưa đủ ngày thì dựng ngày mới **ngay cùng tick**, nếu đủ thì end với `reason:days_complete`.

### 5.2 Pause (mọi mode)

- Cạnh lên `pause` trong `gather`, `quan`, `day`; UI gắn Esc/P. Không xử lý nút lặp khi giữ. Giữ nút qua chuyển pha không tạo cạnh mới.
- **Tick vào pause:** chỉ tăng tick ngoài, cập nhật edge latch, phát `paused`; `sim_tick`, `phase_tick`, lịch gameplay và mọi timer đứng yên.
- **Trong pause:** bỏ qua action edge và `buy`; không cho cá/quái/khách/bếp/Shop tiến tick.
- **Tick resume:** cạnh lên `pause` phát `resumed` và **tiếp tục gameplay ngay trong bước đó**.
- Không tự biến pause thành cơ chế dựa trên đồng hồ UI hoặc gây xê dịch tick headless.

## 6. Test Contract v1.1 — CLI, inputs, scenario, output

### 6.1 CLI

```text
<headless_cmd> --mode gather|quan|day --seed <int>
  [--scenario <file.json>] [--inputs <file.json>]
  [--inventory <file.json>] [--inventory-out <file.json>]
  [--days <N>] --ticks <N> --out <file.jsonl> [--snapshot-every <N>]
```

- `--days` chỉ hợp lệ cho `day`, 1–5, mặc định 1.
- `--inventory-out` chỉ dành gather, `--inventory` chỉ dành quan; day tự bàn giao kho (có thể trong memory) nhưng phải giữ cùng schema như v1.0.
- Mode `gather` độc lập dùng quái của Ngày 1. Mode `quan` độc lập có 6 món.
- Không tự thêm tham số CLI bắt buộc hoặc đổi exit codes v1.0.

### 6.2 Manifest `game.contract.json` — thay đổi bắt buộc

**Chung:** `contract_version:"1.1"`, `team_size:5` nếu TEAM.md chính xác có 5 thành viên, `tick_hz:60`, build/run/headless command vẫn chạy đúng.

**Gather:** `fish_initial` phải là **số 8** (thay cho mảng `fish_initial` v1.0). Thêm `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x`, `fish_depths`, `fish_spawn_x`, `fish_spawn_depths`, `fish_weights`; `fish_yield` đủ 3 loài; thêm N5/N6. `fish_x` là miền x, `fish_spawn_x` là danh sách x.

**Monsters:** `gather.monsters` có `species.ca_sau` gồm `patrol_speed`, `chase_speed`, `detect_radius`, `exit_radius`, `depths`, `hit_radius`, `recoil_ticks`, `recoil_dist`; có `spawns[]` gồm `id`, `kind`, `pos`, `waypoints`, `from_day`; `invuln_ticks:90`, `loss_ratio:0.5`.

**Quan/menu:** B1+B2, T1–T4, ba món mới bên cạnh ba món v1.0, giữ `burn_s:null` trong lõi.

**Day plan:** mảng 5 object `{day,dishes,ingredients}`, `dishes/ingredients` map ID → số nguyên dương, ingredients phải suy được chính xác từ recipe × số suất.

**Shop:** `{max_ticks,upgrades}`, có `oxygen[] {level,price,oxygen_max_s}`, `hp[] {level,price,hp_max}` theo từng cấp.

**Extensions:** Chỉ khai keys/extension đã chọn; không thêm tính năng ngoài lõi vì AI tự suy ra. Đối chiếu chính xác `TICKET-02_original.md` mục 4.1 và 3 trước khi sửa manifest.

### 6.3 Inputs

- Nút mới: `pause` (mọi mode), `shop_done` (Shop), `attack`/`photo` (Gather **chỉ khi extension tương ứng bật**).
- `buy` là **chuỗi khác rỗng** trong frame tương ứng; chỉ thực thi ở frame khai báo, không duy trì như nút. Core nhận `oxygen`, `hp`; vendor nếu bật mới thêm các lệnh mua/bán kind.
- Nút đúng kiểu nhưng sai pha/extension chưa bật thì bỏ qua; dữ liệu sai kiểu/trường không hỗ trợ → mã 2, theo v1.0.
- Latch các nút boolean **không reset qua phase transition**.

### 6.4 Scenario

- `day` nhận cùng `gather` và `quan` làm template fixture **mỗi ngày**.
- `day` block cho phép `{money,earned,reputation,upgrades,day_plan}`. Mặc định money/earned 0, reputation theo tuning, upgrades `{}`, plans preset. Nếu có tiền khởi tạo thì khai cả `money` và `earned`, thỏa `0 ≤ money ≤ earned`.
- `day.day_plan` override theo ngày với `dishes`; tự tính lại `ingredients`, kiểm tra đúng nếu client cũng khai.
- **Cấm** `quan.stock` và `quan.reputation` khi chạy `day`. Kho lấy từ Gather thực tế; quan customers/stoves/orders/menu phải hợp lệ trên kho thực tại lúc chuyển pha, mâu thuẫn → mã 2.
- `gather.player` thêm `invuln_ticks` (và `attack_cd_ticks` chỉ khi Lao extension bật).
- `gather.fish[]` thêm `age_ticks` mặc định 0. `random_fish:false` tắt random fish và cá fixture đứng yên.
- `gather.monsters[]` như mục 3.2.
- Chỉ cho fixture `ca_ho`, `ready_ticks` cháy nếu extension tương ứng bật.

**Fixture mẫu lấy từ Ticket-02** (chỉ minh họa dựng một ngày, không phải chứng minh test đã pass):

```json
{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
```

### 6.5 Output JSONL và events v1.1

- Snapshot cho phép `state:"paused"` ngoài `playing`/`finished`.
- Gather snapshot thêm `monsters[]`, `player.invuln_ticks`, `player.attack_cd_ticks` khi có extension Lao, `ca_ho` khi extension được bật.
- **Trong day** tất cả snapshot có `day`, `day_plan`, `upgrades`, `active_upgrades`; `phase` chỉ là `gather`, `quan`, `shop`. Shop snapshot chứa stock dư và `time_left_ticks` còn lại.
- Snapshot đổi phase ghi **phase mới** với `phase_tick:0`; event kết thúc ghi phase cũ. **Event trong day** có thêm `day` trong vỏ.
- Day start order tại tick khởi tạo: `day_start` → `day_plan` → `phase_start(gather)`.
- Gather kết thúc → dựng Quán, `phase_start(quan)` **cùng tick** (kể cả ngất), Quán gameplay bắt đầu từ **bước sau**.
- Quán kết thúc → dựng Shop, `phase_start(shop)` cùng tick, Shop gameplay từ bước sau.
- Shop kết thúc → dựng ngày kế hoặc kết thúc same tick; end của day có `days_completed`; khi xong đủ ngày: `reason:"days_complete"`.

**Events mới/v1.1 (payload):**

| Event | Data bắt buộc |
|---|---|
| `monster_hit` | `monster_id,hp,lost,pos` |
| `fish_spawned` | `id,kind,pos` |
| `faint` (mở rộng) | `cause:"monster"` hoặc `cause:"choke"`, `lost`, `hp:0` |
| `day_start`, `phase_start` | `{}` |
| `day_plan` | `dishes,ingredients` |
| `paused`, `resumed` | `{}` |
| `bought` | `upgrade,level,price,money` |
| `buy_failed` | `action,reason` (`funds/max_level/out_of_stock/unknown`) |
| `shop_end` | `reason` (`done/time`) |
| `attack`, `monster_stunned` (extension) | `pos,monster_ids` / `monster_id,pos,stun_ticks` |
| `photo`, `released` (extension) | `id,reputation` / `id` |
| `dish_burnt` (extension) | `stove_id,order_id,dish_id,order_status` |
| `vendor_trade` (extension) | `action,kind,price,money` |

**Events cũ** giữ nguyên từ v1.0, đặc biệt `gather_end.inventory`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `customer_left`, `quan_end` và cấu trúc `end`. Không thay đổi tên khóa chỉ để thuận tiện code.

## 7. Hợp đồng giữa 5 phần code (gợi ý tổ chức, KHÔNG phải schema chấm chính thức)

| Người | Phạm vi sở hữu | Inputs cần nhận | Outputs phải bàn giao |
|---|---|---|---|
| **1 – Fish** | Gather fish/nodes, bơi và sinh cá, cập nhật config Gather | seed, phase_tick, player position, hold, config | fish/nodes state + `fish_spawned`, `fish_caught`, `gather`, `node_regrown` |
| **2 – Monster** | Gather monster, hit, invuln, faint | player/hold/HP/oxygen, monster fixture/config | monsters[], HP, hold, `monster_hit`, `faint` |
| **3 – Day** | Orchestrator day, day_plan, Shop, pause/headless & liên kết customer | gather_end inventory, quan_end earnings, Shop actions, config | phase change, retained money/earned/reputation/upgrades, events day/shop/pause |
| **4 – Restaurant** | B1/B2, T1–T4, 6 món, nấu/phục vụ/thanh toán | stock thực, menu/day_plan, customer reserved, shared money/rep | stoves/tables/hand/customers state, events cook/served/paid/quan_end |
| **5 – UI** | Web local HTML/Canvas/CSS, menu/intro/result/shop/HUD | snapshot/event/commands do simulation cung cấp | thao tác user gửi vào simulation, hình ảnh và HUD đúng state |

**Quy tắc tích hợp cần chốt:**

1. **Gather → Quán:** `{ "items": {kind: non_negative_integer} }` (trong day có thể truyền in-memory nhưng phải cùng semantics). `gather_end` có `inventory`, kể cả fainted = `{ "items":{} }`.
2. **Quán ↔ Day:** người 3 điều phối khởi tạo và giữ state xuyên ngày; người 4 quản lý vòng đời đơn và Quán, tuyệt đối không reset tiền/rep khi đang chạy day.
3. **Customer ↔ Kitchen:** `order_id = customer.id`, `order_status` đúng 4 trạng thái; reserved nguyên liệu khi order, tiêu khi `cook_started`; một đơn assigned có chính xác một món ở một bếp hoặc tay; phục vụ đúng order; dọn khi khách rời. Nếu người 3 vẫn sở hữu phần tạo khách, chốt chủ sở hữu hàm theo code thực tế.
4. **UI ↔ Simulation:** đọc snapshot/state và gửi inputs, không suy diễn hoặc hardcode gameplay. Nếu backend chưa có route cho `day`, ghi blocker và thống nhất trước khi thêm API.
5. Người 1/2 cùng khu vực Gather và người 3/4 cùng hệ Quán phải tách hàm/helper hoặc chia ownership theo vùng code để tránh conflict.

## 8. Ma trận test khuyến nghị (ID nội bộ, KHÔNG phải AC chính thức lớp)

| ID | Kiểm chứng | Kỳ vọng |
|---|---|---|
| P2-G01 | Cá đủ 3 loài, 8 đàn đầu, 12 tối đa | đúng config và xuất hiện hợp lệ |
| P2-G02 | age 119→120 / cá đụng mép/góc | đổi hướng/reflect đúng tick, vẫn trong bounds |
| P2-G03 | tick 360,720; hết điểm sinh; clearance 1m | tối đa 1 đàn/suất, không sinh khi không có chỗ |
| P2-G04 | catch ca_keo, giỏ còn 1 ô | `hold_full`, không nhặt nửa đàn |
| P2-M01 | M1 patrol→chase→patrol | đúng khoảng cách/độ sâu/tốc độ |
| P2-M02 | M2 ngày 2 và ngày 3 | ngày 2 không có M2, ngày 3 có M2 |
| P2-M03 | hit với 5 vật, invuln và recoil | rơi floor(5/2)=2 LIFO; -1 HP; 90/60 tick đúng |
| P2-M04 | choke và hit; faint | ngạt không rơi hàng riêng; ngất rơi hết; Quán vẫn mở trong day |
| P2-Q01 | `quan --ticks 0` | 2 bếp, 4 bàn, 6 món cấu hình hợp lệ |
| P2-Q02 | B1/B2 nấu hai đơn đồng thời | timers/assigned độc lập, không trùng nguyên liệu |
| P2-Q03 | T1/T2/T3/T4 cùng có khách | đúng order/bàn, không nhầm tay |
| P2-Q04 | 6 recipes, price, time | đúng số liệu mục 4.1 |
| P2-Q05 | Served tại 50% kiên nhẫn | boa đúng floor 20%, không double-pay |
| P2-Q06 | Closing với eating+waiting | eating thanh toán ngay, waiting closing không trừ uy tín |
| P2-D01 | `day --days 1` và `shop_done` | day_start/plan/phase_start/order transitions/end đúng |
| P2-D02 | D1–D5 | plan/ingredients khớp; Shop đóng mới tăng days_completed |
| P2-D03 | Mua oxygen/hp vừa đủ tiền | bought; earned không đổi; active có hiệu lực ngày sau |
| P2-D04 | Mua thiếu tiền/max level | buy_failed, không đổi tiền/cấp |
| P2-D05 | pause/resume trong Gather/Quán/Shop | outer tick tăng, sim/timer đứng im, resume gameplay ngay |
| P2-D06 | `random_fish:false` và fixtures | cá fixture đứng yên, không sinh tự động |
| P2-I01 | Gather inventory-out → Quan inventory | stock tick0 bằng file kho thật |
| P2-I02 | Cùng seed/input chạy hai lần | output giống nhau từng byte |
| P2-I03 | invalid day scenario/schema/buy/flags | mã 2, không tạo output sai |
| P2-UI01 | Browser local 1280x720 | menu, HUD, Shop, pause và điều khiển thật; ≥30 FPS TB |
| P2-PERF | Headless một ngày không pause | ≤20s cho tối đa 22.200 tick theo máy chấm |

**Bằng chứng:** `docs/proof/phase-2/` chứa logs/test output thật, inputs/scenarios tối thiểu để tái hiện; `docs/verification/phase-2.md` nối từng AC với bằng chứng và kết quả thực tế. Nếu thay test P1 vì số liệu v1.1 đã thay, ghi lý do.

## 9. Smoke test bắt buộc và lệnh mẫu

**9.1 Kiểm tra lệnh chạy thực tế trước**: đọc `headless_cmd` từ manifest/README. Nếu repo dùng `python3 -m chonoi.headless`, có thể dùng lệnh dưới đây; nếu khác, thay cho khớp manifest. Không giả định lệnh mẫu đã được test.

**9.2 Tạo 2 fixture để nối hai tiến trình:**

`dock.json`:
```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
```

`dock-inputs.json`:
```json
{"frames":[{"tick":0,"interact":true}]}
```

Chạy theo `headless_cmd`:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather-p2.jsonl --inventory-out catch-p2.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch-p2.json --ticks 0 --out quan-p2.jsonl
```

**Kỳ vọng:** `catch-p2.json` đúng `{ "items": {"ca_loc":1,"bong_sung":2} }`; snapshot Quán tick 0 có `stock` với hai loại/đúng lượng. Trong v1.1 Gather có monster/fish khác v1.0 nhưng bến được ưu tiên và input tương tác tại tick 0 đóng ca ngay.

**9.3 Day smoke:**

```bash
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day-p2.jsonl
```

Lệnh trên là kiểm tra khởi động và đi hết giới hạn nếu Shop tự đóng; cần thêm fixture/inputs để kiểm tra **nhánh thực sự mua nâng cấp, đóng Shop sớm, các ngày sau**. Không tuyên bố test bếp/Shop pass chỉ vì day mode chạy không lỗi với kho rỗng.

**9.4 Regression/test toàn repo:**

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

- Lưu log thật, số test passed/failed/skipped, command và commit SHA.
- Đối chiếu `game.contract.json` v1.1 với v1.1 TICKET-02, không chỉnh thông số để khớp một test tự viết sai.
- Thử cả `--ticks 0`, invalid scenario, output ordering/timestamp và determinism.

## 10. Extension tùy chọn — chỉ bật khi nhóm chốt

Các extension thuộc **TICKET-02 mục 3**; đây là tóm lược để AI không vô tình làm sai lõi. Chi tiết phải lấy **nguyên văn file `TICKET-02_original.md`**:

| Mã | Nội dung chính |
|---|---|
| `weapon` | Q tấn công, mua 2 cấp giá 300/600, cooldown 180 tick, stun 2/3s, radius 4/6m; xử lý knockback mục tiêu theo ID |
| `net` | Vợt bắt nhiều đàn, mua 250/500, range 4/6m, tối đa 2/3 đàn/lần; giữ luật giỏ/hold_full |
| `snake` | Rắn Hổ Mây M3 từ D1, tuần tra [72,14]↔[76,14], tốc độ chase 3.5m/s, độ sâu [8,20] |
| `burn` | burn_s 20; chỉ cháy khi ready_ticks **>1200**, phải xử lý giữ lại nguyên liệu/đơn |
| `vendor` | Mua/bán từng nguyên liệu trong Shop, giá/thu nhập theo TICKET-02, hàng mua nhập kho Quán tối ngày sau |
| `ca_ho` | Cá Hô H1, release nếu bắt, chụp ảnh 1 lần/ngày tăng 0.5 uy tín, sổ tay 8 loài |
| Settings/SFX | Master/Music/SFX lưu giữa các lần mở game |

**Không tự thêm extension vào `extensions` nếu chưa có code, test và bằng chứng.**

## 11. Phân công team 5 người / tích hợp

- **P2-01 (Người 1):** cá bơi/sinh, cá kèo, kèo nèo, fish tuning, test Gather.
- **P2-02 (Người 2):** Cá Sấu Năm Chèo, hit/recoil/invuln, HP, faint, test an toàn.
- **P2-03 (Người 3):** `day` orchestration, D1–D5, Shop, pause/headless, tích hợp Quán/stock/tiền.
- **P2-04 (Người 4):** B1/B2, T1–T4, 6 món, customer/kitchen/serving, thanh toán, test đa đơn.
- **P2-05 (Người 5):** web local, menu, intros, results, shop, pause UI, HUD, FPS.

**Gợi ý lịch 55 phút:** 0–5 chốt giao diện/plan; 5–20 build song song; phút 20 smoke Gather→Quán và điều phối; 20–35 tích hợp day; 35–45 smoke day & regression; 45–50 retro; 50–55 dự phòng/tag.

**Quy trình Git:** 1 fork chung, từng người commit bằng tài khoản của mình (tối thiểu 3 commit thực chất **trong toàn bộ lab**), review chéo khi sửa file dùng chung, không đụng dữ liệu người khác. Chỉ tag sau khi main chạy được.

## 12. Definition of Done / kiểm tra cuối

- [ ] `game.contract.json` có `contract_version:"1.1"`, `team_size` đúng và tất cả tuning/core keys mới, validate pass.
- [ ] 6 nguyên liệu, 6 món, 6 nút cây; 3 loài cá, cá bơi/sinh; monsters; oxy/HP/ngất đúng.
- [ ] Quán B1+B2, T1–T4, 6 món; orders, phục vụ, tiền/boa/reputation chuẩn.
- [ ] Headless `--mode day`, `--days 1..5`, đúng kế hoạch; Shop/cấp nâng cấp áp dụng ngày tiếp theo.
- [ ] Events, snapshots, pause/resume, phase transition, `days_completed`, JSONL và deterministic đúng.
- [ ] Menu, HUD, Shop, pause, browser local 1280x720; FPS mục tiêu đạt.
- [ ] Smoke hai tiến trình và day smoke có log thực; regression P1 đã rà/ghi lý do thay số chuẩn.
- [ ] Docs: `docs/verification/phase-2.md`, `docs/proof/phase-2/`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, nhật ký từng người cập nhật.
- [ ] Các extension (nếu chọn) có config, README, test và bằng chứng, không ảnh hưởng core.
- [ ] `phase-2` trỏ tới commit main chạy được và đẩy đúng hạn.

## 13. Hướng dẫn ứng xử nếu thiếu thông tin / blocker

- Nếu repo **chưa có TICKET-02 đầy đủ**: dùng `TICKET-02_original.md` trong gói; không lấy con số cũ v1.0 để ghi đè v1.1.
- Nếu dữ liệu `game.contract.json` do thành viên khác sửa: so sánh diff, cập nhật vùng mình sau khi phối hợp; không overwrite toàn file.
- Nếu `quan.py` đang bị người 3 sửa: tách helper Kitchen độc lập, giữ API/input/output hiện có và ghi dependency chính xác.
- Nếu `day --days 1` chưa tồn tại: test độc lập `quan` và fixture đa bàn/bếp, ghi `DAY-INTEGRATION BLOCKED` thay vì khai PASS.
- Nếu không thể xác định một quy tắc còn mơ hồ: ghi câu hỏi cụ thể, ưu tiên hỏi Anh Năm/mentor theo hướng dẫn lab, mô tả giả định tạm trong `docs/clarify.md`.
- Mỗi báo cáo Codex cần: **(1)** file thay đổi, **(2)** AC đạt/chưa đạt, **(3)** lệnh/số test thực, **(4)** bằng chứng, **(5)** blockers/phụ thuộc, **(6)** git status và commit SHA.

---

*Tài liệu tổng hợp phục vụ triển khai. Đối chiếu với `TICKET-02_original.md` và `PRD-0_original.md` trước khi kết luận đủ Test Contract v1.1.*
