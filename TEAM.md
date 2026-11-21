# TEAM — Spec triển khai Chợ Nổi

**Nhóm Ba Khi · 4 người · 4 module · mỗi người điều phối 1 agent.** Điền tên và GitHub handle thật vào bốn dòng dưới đây trước khi mở PR. `team_size` trong [game.contract.json](game.contract.json) đã là 4.

## Phân công

| **Thành viên** | **GitHub handle** | **Module chính** | **Vai quy trình** | **Dự phòng cho** |
|---|---|---|---|---|
|Nguyễn Trung Dũng | … | `sim/gather` | PO · hỏi giảng viên, ghi quyết định | `sim/quan` |
|Nguyễn Văn Lâm | … | `sim/quan` | Integrator · điều phối file chung, tích hợp, gắn tag | `sim/gather` |
|Nguyễn Duy Hưng | … | `client/ui` | Scrum/Release · giữ nhịp, chuẩn bị demo và release | `qa` |
|Đặng Nguyễn Nhật Minh | … | `qa` | QA lead · kiểm thử hộp đen, tổng hợp bằng chứng | `client/ui` |

## Phase 1

Trong 60 phút, làm hai mode chơi độc lập và nối chúng bằng file kho. `gather` là buổi sáng lặn bắt cá, hái rau và mang giỏ về bến. `quan` là buổi tối nấu và phục vụ với một bếp `B1`, một bàn `T1` và ba món. Dùng starter Python và preset hiện có. Ưu tiên lõi và HUD tối thiểu. Phần mở rộng là tùy chọn với nhóm 4 người. [PRD-0 và Test Contract v1.0](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg#phase-1)

### `sim/gather` · Lát 1 và 2 của PRD

Sửa [chonoi/sim/gather.py](chonoi/sim/gather.py). Giữ bơi, gia tốc và chặn biên của starter. Mỗi tick xử lý timer và nút mọc lại → bơi và oxy → E → Space → hết giờ.

1. **Bơi, oxy, Máu và giỏ.** Tính oxy theo độ sâu cuối bước, bắt đầu đếm ngạt ngay ở tick oxy chạm 0. Nổi lên đúng bước ngạt thì hồi oxy và xóa bộ đếm. Ngất làm rơi giỏ theo LIFO, phát `faint` rồi `gather_end` với kho rỗng.
2. **Hái, bắt cá và bàn giao kho.** Nút về 0 có thể hái ngay. E xét bến trước rồi mới xét hái ở mặt nước. Space bắt đàn gần nhất khi đang lặn và hết hồi chiêu. Khoảng cách hòa xử lý theo ID. Bắt đủ cả đàn hoặc phát `hold_full` và giữ nguyên đàn cùng hồi chiêu. Lượt hợp lệ ở bước cuối vẫn vào kho. Cập bến và hết giờ chốt giỏ qua giao diện runner hiện có.

**Bàn giao cho QA và Quán.** Fixture ngạt ở tick biên, giỏ đầy, hái hoặc bắt hợp lệ ở bước cuối và cập bến đúng mép. Trước phút 25, xuất một file kho thật và đối chiếu với `gather_end.data.inventory`.

### `sim/quan` · Lát 3 và 4 của PRD

Sửa [chonoi/sim/quan.py](chonoi/sim/quan.py). Bắt đầu bằng [kho mẫu](docs/contracts/inventory.sample.json) hoặc fixture `quan.stock`. Mỗi tick xử lý timer và bếp chín → di chuyển và E → thanh toán, khách rời hoặc đóng ca → khách mới nếu còn giờ. Đọc công thức, giá và timer từ `tuning.menu` và `tuning.quan`.

1. **Khách, giữ chỗ và kiên nhẫn.** Dựng khách fixture và phần giữ nguyên liệu theo mục D. Tính kho khả dụng từ tồn vật lý trừ phần giữ. Nếu còn giờ, xét khách cuối bước theo lịch `phase_tick`. Khách chọn đều theo seed trong các món đủ nguyên liệu và giữ đúng công thức ngay. Bàn bận bỏ lượt. Bàn trống mà thiếu món phát `no_dish`. Khách bỏ đi do hết kiên nhẫn làm giảm uy tín và nhả phần giữ chưa dùng.
2. **Bếp, phục vụ và tiền.** Mỗi cạnh E chọn tối đa một đối tượng theo khoảng cách, ưu tiên bếp rồi ID khi hòa. Bếp idle nhận đơn `reserved` cũ nhất và trừ nguyên liệu đã giữ. Nấu xong, bưng khi tay trống, giao đúng `order_id`. Xét phục vụ trước bỏ đi hoặc đóng ca để chấp nhận đúng tick biên. Chốt boa lúc giao, thu tiền và cộng uy tín khi khách trả. Đóng ca thu tiền của khách đang ăn, dọn khách chờ với lý do `closing`, rồi phát `quan_end`.

**Bàn giao cho QA và UI.** Fixture gọi món → nấu → bưng → phục vụ → trả tiền, thiếu món, hết kiên nhẫn và đóng ca. Phối hợp kiểm dữ liệu fixture mục D, gồm món ở bếp/tay phải khớp đơn và giữ chỗ không vượt tồn. Snapshot trả trạng thái kho, đơn, bếp, bàn và tay theo mục E.

### `client/ui` · Chơi thử, HUD và README

Sửa [chonoi/web/](chonoi/web/) dựa trên snapshot mẫu ngay từ kickoff. Dùng mặt cắt ngang cho sông và góc nhìn trên xuống cho quán. Kiểm WASD/mũi tên, E, Space và R. Khi sim có dữ liệu thật, chơi lại cả hai mode qua `chonoi.live`.

- Gather hiện thời gian, oxy, Máu và giỏ. Quán hiện kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền và uy tín. `stock` trong snapshot là tồn vật lý. HUD hiển thị phần còn dùng được sau khi trừ `customers[].reserved`.
- Bàn giao demo hai mode và cập nhật [README.md](README.md) với đường chạy từ clone sạch trong tối đa 3 lệnh trên macOS/Linux, điều khiển, cách tính điểm và lệnh test. Ghi nguồn asset vào [CREDITS.md](CREDITS.md) nếu dùng asset ngoài.

### `qa` · Hộp đen và bằng chứng

Dùng [tests/](tests/), [ma trận Phase 1](docs/verification/phase-1.md) và [thư mục bằng chứng](docs/proof/phase-1/). Viết fixture từ lúc kickoff. Giữ smoke test công khai và bổ sung ca biên của hai sim theo mục D–G.

- **Test Contract.** Kiểm tick 0 và tick dừng, event trước snapshot cùng tick, hành động theo cạnh nhấn, JSONL và kho lặp lại giống từng byte. Fixture sai hoặc mâu thuẫn trả mã 2 trước khi ghi đầu ra. Kiểm thứ tự và tick của `faint`, phục vụ đúng deadline và dọn ca đúng lý do.
- **Smoke hai tiến trình.** Với seed 42, dựng giỏ `["ca_loc","bong_sung","bong_sung"]` và nhấn E ở input tick 0. Chạy gather tối đa 1 bước, dùng file nó ghi để chạy quan `--ticks 0`. `stock` ở snapshot đầu phải là `{"bong_sung":2,"ca_loc":1}`. Kiểm thêm giới hạn tick trước `gather_end` giữ nguyên file đích.
- **Bàn giao.** Chạy suite và smoke trên commit chuẩn bị gắn tag ở `main`. Lưu lệnh, SHA, kết quả và đường dẫn bằng chứng theo từng AC. Đánh dấu đạt hoặc chưa đạt sau khi chạy. Cùng Scrum/Release kiểm lại HUD và README theo DoD.

### Mốc bàn giao Phase 1

| **Phút** | **Việc chốt** |
|---|---|
| 0–15 | Điền tên, GitHub handle, kênh nhóm và giờ standup. Đọc mục D–G, thống nhất giao diện bên dưới. Quán dùng kho mẫu, UI dùng snapshot, QA dựng fixture để cả bốn agent bắt đầu ngay. |
| 15–45 | Triển khai song song. Phút 20 rà vướng mắc, phút 25 thử kho thật. Standup giữa phase vào phút 30 theo mặc định. |
| 45–55 | Gộp và chơi thử hai mode trên `main`. QA chạy smoke và cập nhật ma trận. Mỗi người cập nhật nhật ký AI và phản tư. Scrum/Release tổng hợp retro. |
| 55–60 | Integrator đẩy tag `phase-1` trỏ tới commit bàn giao trên `main` chậm nhất `1:00` tính từ đầu phase. |

## Giao diện dùng chung

Các bảng dưới đây dùng cho Phase 1. Đối chiếu định dạng và hành vi với mục B–G của [Test Contract v1.0](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg#phase-1). Số liệu lấy từ [game.contract.json](game.contract.json) hoặc fixture hợp lệ.

### API giữa các module

| **Điểm nối** | **Chữ ký và trách nhiệm** |
|---|---|
| Runner → Gather | `GatherSim(tuning, scenario, streams, ids)`. `inventory_items()` trả map `kind → số lượng`. Runner bọc map trong `items` và ghi file. |
| Runner → Quán | `QuanSim(tuning, scenario, streams, ids, inventory=None)`. `inventory` là map đã đọc từ `items`. `scenario` đã được bóc khối theo mode, nên bên trong sim đọc `scenario.get("stock")`. |
| Cả hai sim → runner | `step(inp: InputState)` trả danh sách `(name, data)` theo thứ tự xảy ra. `snapshot()` trả các trường riêng của mode. Runner đọc `mode`, `phase`, `done`, `reason`, `time_left_ticks`, `money`, `earned`, `reputation`. |
| Runner → headless/live | Cùng dùng `Session(mode, tuning, scenario, seed, inventory=None)`. `Session.step(inp)` gắn `type`, `tick`, `phase` cho event. `Session.snapshot()` ghép trường chung với trường riêng. |
| Live → UI | `GET /state` trả snapshot kèm `meta` (tuning của mode), `events` (các event gần đây, có thể lặp giữa lần đọc), `finished` (boolean), `reason` và `error` (chuỗi hoặc `null`). UI lấy snapshot làm trạng thái hiện tại. |
| UI → live | `POST /input` gửi object như `{"move":[0,1],"interact":false,"catch":true}`. Trường có mặt cập nhật trạng thái phím đang giữ. `POST /restart` với body rỗng bắt đầu lại cùng seed, scenario và kho đầu lượt. Hai POST trả `200 {"ok":true}` khi thành công. Payload `/input` sai kiểu trả `400 {"error":"…"}`. |

`InputState.move` là vector đã chuẩn hóa. Hai thành phần trong `[-1,1]`; độ dài trên 1 được chuẩn hóa về 1. `pressed("interact")` và `pressed("catch")` báo cạnh nhấn `false → true`. E dùng cho cả hai mode, Space (`catch`) chỉ tác động trong gather, R chỉ gọi live restart.

### Tên trường, ID và đơn vị

- Dùng `snake_case` cho khóa JSON, tên event và giá trị enum. Giữ nguyên chính tả khi đi qua Python, HTTP, UI và fixture. Tên hiển thị có thể dịch ở UI. Dùng `id` trên thực thể và các khóa tham chiếu như `node_id`, `fish_id`, `stove_id`, `table_id`. `order_id` là ID của khách, còn `tables[].customer_id` trỏ đến `customers[].id`.
- Giữ các ID preset `N1`…`N4`, `F1`…`F6`, `B1`, `T1`. Quy ước nhóm dùng họ `C` cho khách tự sinh, ví dụ `C1`. Nạp ID fixture vào `IdAllocator` trước khi cấp ID mới. Dùng `ids.sort_by_id` để sắp theo tiền tố, hậu tố số ASCII (vắng tính `-1`) và ID gốc. Ví dụ `F2` đứng trước `F10`. Giữ `hold` theo thứ tự nhặt và sắp mã món hoặc nguyên liệu theo thứ tự Unicode khi contract yêu cầu.
- **Mã nguyên liệu** gồm `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. **Mã món** gồm `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`. Đọc công thức bằng `tuning.menu[dish_id].recipe`.
- Vị trí `pos` tính bằng mét và vận tốc `vel` tính bằng m/s. Gather dùng `[x,d]` với `d` dương hướng xuống và `heading_deg` là góc từ `+x`. Quán dùng `[x,z]` với `z` dương hướng bắc. Trường `*_ticks` hoặc `*_tick` dùng số nguyên; `*_s` trong tuning dùng giây và được quy đổi ở 60 Hz. Giữ độ chính xác khi tính toán, làm tròn tọa độ khi xuất JSONL đến 3 chữ số thập phân.
- Tiền, giá, boa và điểm là số nguyên. Tiền tính theo nghìn đồng. `reputation` có thể có phần lẻ. `score = earned + reputation_multiplier × floor(reputation)`. Dùng `null` cho tham chiếu hoặc ô món đang trống, `[]` cho danh sách rỗng, `{}` cho map rỗng.

### Snapshot và fixture dùng chung

| **Phạm vi** | **Khóa và kiểu dữ liệu** |
|---|---|
| Snapshot chung | `type: "snapshot"`, `tick`, `sim_tick`, `phase_tick`, `mode`, `phase`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`. Phase 1 dùng `gather` hoặc `quan` cho `mode` và `phase`. `state` là `playing` hoặc `finished`. |
| Gather · `player` | `pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `catch_cd_ticks`, `at_surface` (boolean). |
| Gather · thực thể | `hold` là mảng mã nguyên liệu, mới nhất ở cuối. `hold_count` và `hold_capacity` là số ô. `nodes[]` có `id`, `kind`, `pos`, `regrow_ticks`, `ready` (boolean, đúng khi `regrow_ticks == 0`). `fish[]` có `id`, `kind`, `pos`, `heading_deg`. |
| Quán · người chơi và kho | `player` có `pos`, `vel`. `stock` là map tồn vật lý gồm cả phần đang giữ. `hand` là payload món hoặc `null`. HUD tính kho khả dụng theo từng `kind` bằng `stock` trừ tổng `customers[].reserved`, xem mã vắng là 0. |
| Quán · bếp và bàn | `stoves[]` có `id`, `pos`, `state` (`idle`, `cooking`, `ready`), `dish` (payload món hoặc `null`), `cook_ticks_left`, `ready_ticks`. `tables[]` có `id`, `pos`, `customer_id` (ID khách hoặc `null`). |
| Quán · `customers[]` | `id`, `table_id`, `dish_id`, `order_tick`, `state` (`waiting`, `eating`), `patience_ticks_left`, `eat_ticks_left`, `order_status` (`reserved`, `assigned`, `unfulfillable`, `served`), `reserved` (map `kind → số lượng`), `base_price`, `tip`. Chỉ liệt kê khách còn ngồi. `base_price` và `tip` phải có giá trị đã chốt khi khách đang ăn. |
| Payload món ở `hand` và `stoves[].dish` | `{order_id, dish_id, base_price}`. `base_price` là giá món trước boa. |

Fixture JSON có một khối gốc trùng mode, ví dụ `{"gather":{"hold":["ca_loc"],"random_fish":false}}`. `nodes`, `fish`, `customers` thay cả danh sách mặc định. `stoves` và `tables` cập nhật theo ID đã có. Hai cờ `random_fish:false` và `random_customers:false` tắt phần mặc định tương ứng và giữ các thực thể đã khai trong fixture. Các trường suy ra khi chạy như `hold_count`, `ready` và `customer_id` do sim tạo. Dùng mục D để kiểm giá trị mặc định và liên kết hợp lệ trước snapshot tick 0.

### Sự kiện và dòng kết thúc

Chung một dạng `{type: "event", tick, phase, name, data}`. Gather và Quán phát event, runner gắn thông tin của tick. QA đọc JSONL và UI dùng `events` trên live để hiển thị phản hồi.

| **`name`** | **Trường trong `data`** |
|---|---|
| `dive`, `surface` | `pos` sau di chuyển. |
| `oxygen_empty`, `choke` | `oxygen_ticks: 0` khi vừa cạn oxy, hoặc `hp` sau khi ngạt trừ Máu. |
| `faint` | `cause: "choke"`, `lost` (mảng mã nguyên liệu theo LIFO), `hp: 0`. |
| `gather`, `node_regrown` | `gather` có `node_id`, `kind`, `amount`. `node_regrown` chỉ có `node_id`. |
| `fish_caught` | `fish_id`, `kind`, `yield` (số nguyên liệu lấy từ đàn). |
| `hold_full` | `action` (`gather` hoặc `catch`), `node_id` hoặc `fish_id` theo hành động, `required`, `free`. |
| `gather_end` | `reason` (`time`, `docked`, `fainted`), `inventory` (object có `items`). |
| `customer_arrived`, `no_dish` | `customer_arrived` có `order_id`, `table_id`, `dish_id`. `no_dish` dùng object rỗng `{}`. |
| `cook_started`, `dish_ready`, `dish_picked` | Cả ba có `stove_id`, `order_id`, `dish_id`. `cook_started` thêm `items` (mảng mã nguyên liệu, có lặp theo lượng, sắp theo mã) và `base_price`. |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip`. |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`, `closing`). |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`, `closing`), `reputation`. |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation`. |

```json
{"type":"event","tick":1,"phase":"gather","name":"gather","data":{"node_id":"N1","kind":"bong_dien_dien","amount":1}}
```

Dòng cuối là `{type: "end", ticks, sim_tick, mode, state, reason, money, earned, reputation, score}`. `reason` lấy từ kết thúc gameplay nếu có, kể cả khi trùng bước cuối được cấp. Nếu chỉ chạm `--ticks`, dùng `reason: "tick_limit"` và `state: "playing"`.

### Headless và file kho

```text
<headless_cmd> --mode gather|quan --seed <int> --ticks <N> --out <file.jsonl>
  [--scenario <file.json>] [--inputs <file.json>] [--snapshot-every <N>]
  [--inventory <file.json>] [--inventory-out <file.json>]
```

- File inputs có dạng `{"frames":[{"tick":0,"move":[0,1]},{"tick":30,"catch":true},{"tick":31,"catch":false}]}`. `tick` tăng nghiêm ngặt từ số nguyên không âm. Frame vắng trường thì giữ giá trị cũ. Mặc định `move` là `[0,0]` và hai nút là `false`.
- Input tick `k` tạo event và trạng thái ở `k+1`. Headless ghi snapshot sau dựng fixture ở tick 0, ở bội số `--snapshot-every` (mặc định 10) và ở tick dừng. Mỗi tick tối đa một snapshot, event đứng trước snapshot cùng tick. `--ticks 0` chỉ dựng fixture. Mã thoát `0` là chạy thành công, `2` là đối số hoặc dữ liệu không hợp lệ, `1` là lỗi thực thi hoặc ghi. Lỗi dữ liệu xác định lúc khởi tạo được báo qua stderr trước khi ghi JSONL hoặc kho.
- File kho JSON chỉ có khóa gốc `items`, ví dụ `{"items":{"bong_sung":2,"ca_loc":1}}`. Số lượng nguyên không âm, mã vắng tính 0, bên ghi bỏ lượng 0. Gather ghi `--inventory-out` một lần bằng thay thế nguyên tử sau `gather_end`; nội dung khớp `data.inventory`. Nếu chạm giới hạn bước trước khi kết thúc, file đích giữ nguyên. Quán nạp `--inventory` hoặc `quan.stock` trong fixture; khai cả hai trả mã 2. [Kho mẫu](docs/contracts/inventory.sample.json)
- Seed, tham số và nội dung đầu vào giống nhau trên cùng bản chạy và máy phải cho JSONL UTF-8 và file kho giống từng byte. Dùng `Streams` theo mục đích, sắp ứng viên trước khi chọn, giữ thời gian thực ở live adapter và tắt tính năng sáng tạo ở headless.

### Khi thay đổi giao diện

Integrator phối hợp với module phát và module đọc trước khi sửa file chung (`runner`, `scenario`, `inputs`, `inventory`, CLI, live adapter). Ghi tên trường, kiểu, trường hợp rỗng, ví dụ payload và fixture xác nhận trong cùng PR. UI kiểm snapshot qua `/state`, QA kiểm payload và tick qua headless. Starter hiện cần bổ sung `quan.player.vel` để khớp bảng. `gather.player.invuln_ticks` là trường riêng của starter, UI và QA dựa vào các trường v1.0 ở trên.

## Thỏa thuận làm việc

- **Kênh chat nhóm** · … (điền khi kickoff). Vướng quá 10 phút thì gửi lệnh tái hiện và nhờ người dự phòng hỗ trợ. PO hỏi Anh Năm trên lab board hoặc giảng viên và ghi quyết định ở [docs/clarify.md](docs/clarify.md). Integrator chốt phương án kỹ thuật sau khi trao đổi với các module liên quan.
- Mỗi người mở nhánh ngắn `codex/<module>-<ticket>` từ `main`. Giao agent đúng ticket, phạm vi file, PRD phase, mục giao diện ở trên và [AGENTS.md](AGENTS.md). Ai cần file chung thì trao đổi với Integrator trước để tránh cùng sửa một file.
- Người phụ trách đọc diff của agent, chạy ca module và suite chung, ghi kết quả trong mô tả commit hoặc `docs/proof/`. Người dự phòng review PR trước khi Integrator gộp. Mỗi người có ít nhất 3 commit có nội dung trong lab. Ghi phần AI tham gia vào [docs/ai-usage-log.md](docs/ai-usage-log.md).
- Mỗi phase, QA cập nhật ma trận AC và kết quả thực tế trong `docs/verification/phase-N.md`. Integrator kiểm bản tích hợp rồi gắn tag từ `main` theo [lịch lab](README.md). Hạng mục chưa đạt ghi vào bằng chứng của phase. Chốt release `v1.0.0` cùng Phase 4.

## Lệnh kiểm tra chung

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it -v
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory docs/contracts/inventory.sample.json --out quan.jsonl
python3 -m chonoi.live --mode gather  # đổi thành quan để thử buổi tối
python3 tools/check_team.py
```

Lệnh suite trên dùng cú pháp Bash. Trên PowerShell, đặt `$env:PYTHONPATH = 'tests;.'` trước khi chạy. Suite hộp đen gọi `python3` theo `headless_cmd`, nên môi trường chạy suite cần tìm được lệnh này trên `PATH`. Lệnh `check_team.py` cần bốn tên và handle thật.
