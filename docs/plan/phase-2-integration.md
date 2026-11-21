# Giao diện tích hợp Phase 2 · Test Contract v1.1

[PHASE2.md](../../PHASE2.md) thay các điều khoản v1.0 được nêu trong ticket. Dùng lại [PRD Phase 1](../../PHASE1.md) cho các luật còn hiệu lực. Các chữ ký dưới đây là phương án nội bộ cho starter Python.

## Quyết định kỹ thuật để triển khai

| Chi tiết | Phương án dùng chung | Người phụ trách |
|---|---|---|
| Snapshot `day_plan` | Dùng `{dishes,ingredients}` như payload event; lấy số Ngày ở trường `day` bên ngoài. | 4 |
| Fixture Quán lỗi sau khi đã chạy Gather | Trả mã 2 theo mục 4.3. Ghi JSONL của `day` vào file tạm để giữ nguyên file đích nếu fixture không hợp lệ. | 4 |
| Cảnh báo “Thủy quái!” | HUD dùng bán kính phát hiện của loài và điều kiện độ sâu. | 3 |
| `attack` và `photo` khi tắt mở rộng | Chấp nhận giá trị boolean và bỏ qua hành động theo mục 4.2. Trường lạ hoặc sai kiểu trả mã 2. | 4 |

Nếu bộ chấm có yêu cầu khác về giao diện test, Integrator đối chiếu với ticket và hỏi giảng viên về điểm cụ thể.

## Thay đổi so với Phase 1

| Phần | V1.1 | Hồi quy còn hiệu lực |
|---|---|---|
| Gather | `fish_initial` đổi từ danh sách thành số `8`. Có 3 loài cá bơi/sinh, 6 nút, Cá Sấu M1 và M2 từ D3, sát thương và bất tử. | Di chuyển/chặn biên, hồi oxy, ngạt, cạnh nút, bến trước hái/bắt/hết giờ, bắt cả đàn và đủ chỗ, ngất mất giỏ. Tắt cá động bằng fixture `random_fish:false`; dùng `monsters:[]` để cô lập các test cũ. |
| Kho và Quán | Giữ schema kho, mở danh sách hợp lệ thêm `ca_keo`, `keo_neo`. Quán có 2 bếp, 4 bàn, 6 món. `day` giới hạn món theo kế hoạch, số suất chỉ dùng cho mục tiêu thu gom. | Hai tiến trình vẫn dùng `--inventory-out` và `--inventory`. Kho cũ vẫn đọc được. Giữ chỗ nguyên liệu, thứ tự tương tác, thanh toán, boa và uy tín theo v1.0. |
| CLI và output | Thêm `day`, `--days 1..5` mặc định 1, pause cả ba mode, mua/đóng Shop. Event `day` thêm `day`, snapshot thêm các trường ở mục 4.4. | Cùng đầu vào cho output giống từng byte. Giữ CLI, output và mã thoát của mode độc lập ở các phần không đổi. Test cũ trông đợi từ chối `day` chuyển sang kiểm `day` hợp lệ và `--days` sai mode/phạm vi; vẫn kiểm mode lạ. |

### Dữ liệu trong manifest và file kho

- Giữ các khoá cũ trong `tuning` và đặt `contract_version:"1.1"`. `tuning.gather` có `fish_initial:8`, `fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_ticks`, `fish_spawn_clearance`, `fish_x`, `fish_depths`, `fish_spawn_x`, `fish_spawn_depths`, `fish_weights`, `fish_yield` và `nodes`. Map theo loài có đủ `ca_linh`, `ca_loc`, `ca_keo`. Dữ liệu khe sinh là tích của danh sách `fish_spawn_x` và độ sâu của từng loài. Chọn 8 vị trí hình học khác nhau lúc đầu; khi sinh định kỳ xét khoảng cách nghiêm ngặt `> 1 m` trước khi chọn loài theo trọng số.
- `tuning.gather.monsters = {species,spawns,invuln_ticks,loss_ratio}`. `species.ca_sau = {patrol_speed,chase_speed,detect_radius,exit_radius,depths,hit_radius,recoil_ticks,recoil_dist}`. `spawns[] = {id,kind,pos,waypoints,from_day}`. `recoil_dist` tính cho cả đợt lùi; chia cho `recoil_ticks` để lấy quãng đường mỗi bước.
- `tuning.quan` khai bếp, bàn và số chuẩn; `tuning.menu[dish_id] = {recipe,cook_s,price}`. `tuning.day_plan[] = {day,dishes,ingredients}`; tích từng công thức với số suất rồi cộng theo nguyên liệu. `tuning.shop = {max_ticks,upgrades}`; `oxygen[] = {level,price,oxygen_max_s}`, `hp[] = {level,price,hp_max}`, theo cấp tăng dần. Kiểm preset và override theo cùng cách tính nguyên liệu.
- File kho là `{"items":{"bong_sung":2,"ca_keo":2,"keo_neo":1}}` hoặc map tương đương. Số đếm nguyên không âm; khóa vắng là 0; bên ghi bỏ mục 0. Dùng danh sách 6 ID nhất quán khi kiểm file, `hold`, `stock`, `reserved` và công thức. `stock` vẫn là tồn vật lý, khả dụng bằng tồn vật lý trừ tổng giữ chỗ. `day` truyền map `items` trong bộ nhớ và cấm cả hai cờ file kho.

## Chữ ký để làm song song

### Người 1 ↔ 2 · Gather

| Chủ | Giao diện | Trách nhiệm |
|---|---|---|
| 1 | `init_fish(sim, scenario) -> list[dict]`, `advance_fish(sim, phase_tick, events)` trong `gather_resources.py` | Dựng và reserve ID cá; mỗi cá có `{id,kind,pos,heading_deg,age_ticks}`, tuổi mặc định 0. Giữ `tick_resources`, `harvest`, `catch_fish` từ P1. `advance_fish` bơi rồi sinh theo lịch, phát `fish_spawned` khi sinh định kỳ. `random_fish:false` tắt cá mặc định và cả bơi/sinh, vẫn giữ cá fixture. Tách luồng seed khởi tạo, đổi hướng và sinh; duyệt theo ID. |
| 2 | `init_monsters(sim, scenario, day_number) -> list[dict]`, `advance_monsters(sim, events)` trong `gather_monsters.py` | Quái có `{id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}`. `monsters:[]` tắt quái fixture. Cập nhật theo ID, sau đó chọn tối đa một hit gần nhất, hòa theo ID. Giảm máu, bỏ hàng LIFO, đặt bất tử, phát `monster_hit`. Chủ vòng Gather gọi kết thúc khi máu về 0. |
| 2 | `GatherSim(tuning, scenario, streams, ids, *, day_number=1, active_upgrades=None)` | Tính mức oxy/máu hiệu lực cho ca mới từ dữ liệu Shop. Dựng cảnh với giá trị mặc định đầy; kiểm giới hạn fixture theo cấp đang áp dụng. Giữ `inventory_items()` trả map đếm và `snapshot()` thêm quái, tuổi cá, bất tử. |

Thứ tự trong `GatherSim.step` sau khi tăng `phase_tick`: giảm giờ/cooldown/bất tử và hồi nút → di chuyển/oxy/ngạt → quái → bến/hái → bắt tại vị trí cá trước khi bơi → hết giờ → cá bơi/sinh nếu chưa kết thúc. Trừ máu do ngạt kể cả khi đang bất tử, ngạt thường không làm rơi đồ. Khi máu về 0, phát `faint` theo nguyên nhân `choke` hoặc `monster`, bỏ phần giỏ còn lại, rồi `gather_end`. Lùi bắt đầu từ bước sau khi hit, hết lùi thì bước kế mới phát hiện hoặc chạm lại. Dùng log event sao chép các tọa độ có thể còn thay đổi.

### Người 2/3 ↔ 4 · Scenario, Quán và vòng Ngày

- `load_scenario(path, mode, tuning)` trả một khối đã chuẩn hóa cho mode độc lập; với `day` trả `{day:{...},gather:{...},quan:{...}}` với mặc định rỗng. Người 2 kiểm cấu trúc và miền; dùng hàm chuẩn hóa kế hoạch của người 4 hoặc để `DaySim` gọi khi dựng. Mỗi Ngày dựng lại từ bản sao của mẫu. Người 3 kiểm khách, đơn, bếp, món đang cầm trên **kho thực và menu thực lúc vào Quán**. `BadInput` trả mã 2, kể cả khi phát hiện sau Gather.
- `QuanSim(tuning, scenario, streams, ids, inventory=None, *, allowed_dishes=None)` nhận kho dạng map đếm và tập ID món. Dựng `sim.menu` giới hạn trước khi nạp khách/đơn; `None` dùng cả 6 món. Mỗi ca đặt `shift_earned=0`. Người 4 khởi tạo và đồng bộ `money`, `earned`, `reputation` giữa Day và ca con; người 3 giữ cách tính tiền và thứ tự v1.0 trong Quán. Có thể thử Quán độc lập bằng kho mẫu mà không cần Day.
- `resolve_day_plans(tuning, overrides=None) -> dict[int, dict]` trong `day.py` trả các kế hoạch theo Ngày, tính lại nguyên liệu từ công thức và kiểm giá trị khai. `DaySim` giữ `day`, `days_completed`, `phase`, `phase_tick`, `money`, `earned`, `reputation`, `upgrades`, `active_upgrades`. `upgrades` là map cấp đã mua; `active_upgrades` là bản sao tại lúc dựng Ngày. Cấp vắng tính 0. `ShopSim` nhận kho dư, số dư và cấp đã mua; cập nhật một lệnh mua trước xét đóng Shop. Chỉ đóng Shop mới tăng `days_completed`, kể cả Ngày cuối. Kho dư bỏ khi qua Ngày.
- `Session` dùng chung cho live và headless. Input tiếp tục cập nhật trạng thái giữ nút ở mọi tick ngoài, kể cả lúc pause và chuyển pha. Thêm `InputState.buy: str | None` chạy một lần tại frame khai báo. Cạnh pause xử lý trước mọi hành động; bước vào pause chỉ tăng `tick`, bước resume phát `resumed` rồi chạy gameplay. `sim_tick` chỉ tăng khi gameplay chạy, `phase_tick` đặt 0 khi đổi pha. Dùng một `Streams` và `IdAllocator` cho mỗi lượt, duy trì qua các ca trong Day.
- Vỏ event Day cần giữ `phase` và `day` **lúc phát**, kể cả khi chuyển pha trong cùng tick. Mở lượt: `day_start → day_plan → phase_start(gather)` tại tick 0, trước snapshot. Kết Gather/Quán: event kết ca cũ, rồi `phase_start` pha mới; snapshot chuyển pha luôn ghi pha mới ở tick pha 0, kể cả ngoài nhịp snapshot định kỳ. Snapshot Shop có `stock` dư và `time_left_ticks`. Snapshot mọi pha của `day` có `day`, `day_plan`, `upgrades`, `active_upgrades`. Shop kết thúc ghi `shop_end` rồi dựng Ngày kế ở cùng tick nếu còn Ngày. `end` luôn cuối, thêm `days_completed` và lý do `days_complete` khi đủ Ngày.

### Người 3 ↔ 4 · Browser và HUD

- Giữ `GET /state`, `POST /input`, `POST /restart`. Người 4 cấp snapshot hiện tại và event gần nhất với tag tick/pha/Ngày. Dùng `meta = tuning[phase]` theo pha hiện hành, `presentation` chỉ ở live cho phần trình bày. Input là `{move:[a,b],interact:boolean,catch:boolean,pause:boolean,shop_done:boolean,buy:string}`; các trường có thể vắng. `buy` là lệnh một lần, còn `pause` và `shop_done` là cạnh lên.
- Chốt giao diện nội bộ cho hai agent: `presentation = {screen,day_result,summary}`. `screen` nhận `menu/day_intro/gather/evening_intro/quan/day_result/shop/summary`. `day_result` nhận `{served,left,shift_earned,tip,reputation_delta}` hoặc `null`; `summary` nhận `{money,earned,score,reputation,top_dishes}` hoặc `null`, `top_dishes` là mảng ID đồng hạng bán chạy. Client gửi `POST /presentation` với `{action:"advance"}` để chơi/tiếp tục qua màn giới thiệu hoặc kết quả, hoặc `{action:"menu"}` để về menu. Backend chờ ở các màn này và xét hành động theo màn hiện tại. Client cho DayIntro tự gửi `advance` sau 4 giây hoặc khi nhấn phím, một lần cho mỗi lần vào màn. `POST /restart` làm mới lượt. Nút Thoát trả về màn menu/kết thúc phiên chơi trong trình duyệt theo khả năng của môi trường.
- Các màn chờ thuộc live, dùng cổng trình bày riêng để tránh làm trôi timer và tránh phát sự kiện `paused` chỉ vì đang xem giới thiệu. Pause gameplay bằng nút riêng. Headless chỉ chạy `gather,quan,shop`.
- HUD dùng số giỏ theo loại với `day_plan.ingredients`, trạng thái quái và oxy, bàn và bếp theo ID, tiền ca và kho khả dụng. DayResult/Summary lấy số liệu từ event nghiệp vụ, gồm phục vụ, khách rời, thu tiền, boa, uy tín và món bán chạy; backend live tổng hợp theo lượt để cửa sổ event gần nhất không làm mất số liệu. Kiểm các ngưỡng cảnh báo và chữ không chân tối thiểu 18 px tại 1280×720 theo ticket.
- Hướng mỹ thuật dùng để dựng UI: 2D phẳng, cảnh Gather nhìn ngang với nâu phù sa, xanh dừa và hồng sớm; Quán nhìn từ trên xuống, gỗ nâu và vàng đèn. Giữ cùng dấu hiệu nhận diện Út Sen ở hai cảnh. Người 3 phụ trách phần vẽ và ghi nguồn tài sản nếu dùng.

## Smoke và kiểm chứng

Phút 20 dùng fixture ở bến chứa `["ca_loc","bong_sung","bong_sung","ca_keo","keo_neo"]` và input có cạnh `interact` tại tick 0. Chạy Gather `--ticks 1 --inventory-out catch.json`, rồi Quán `--ticks 0 --inventory catch.json`. So `gather_end.inventory`, file và `stock` ở snapshot tick 0; lưu bằng chứng `integration.*`.

Sau khi tích hợp, chạy các lệnh sau bằng bản v1.1 và lưu kết quả thật. JSONL bị Git ignore, có thể lưu trích xuất có kiểm chứng thành `.txt` hoặc ghi đính kèm trong proof.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
time python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out /tmp/p2-day-one.jsonl
python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 111000 --out /tmp/p2-day-five.jsonl
python3 -m chonoi.live --mode day --days 5
```

Kiểm kịch bản nâng cấp riêng bằng fixture có tiền và ca ngắn: mua đúng giá, kiểm tiền giảm còn `earned` và điểm giữ nguyên, cấp mua hiện ngay nhưng oxy/máu chỉ tăng ở Ngày kế. Thử pause giữ timer/edge và mua rồi đóng Shop ở bước cuối. Chạy một lượt giống hệt lần nữa để so byte. Mốc hiệu năng theo ticket là một Ngày headless ≤ 20 s trên máy chấm và live ≥ 30 FPS trung bình tại 1280×720; lưu số đo cùng mô tả môi trường.
