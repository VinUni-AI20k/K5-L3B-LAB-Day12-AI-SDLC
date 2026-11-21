# Research Phase 1 — luật, Test Contract, rủi ro

> Người viết: worker RESEARCH (Claude), chỉ đọc code. Ngày 2026-11-21, branch `tv6/phase-1-team-ai`.
> **Số dòng dẫn theo commit `f0a1906` (HEAD)**. `chonoi/sim/*.py` có thể đang được worker code sửa song song, nên số dòng ở đó có thể lệch; tìm theo chuỗi `TODO(nhóm`.
> PRD-0 trên lab board không đọc được. Những gì không có trong starter/contract/test được đánh dấu **GIẢ ĐỊNH** hoặc **CÂU HỎI**.

## 0. Kết quả chạy (bằng chứng)

| Lệnh | Kết quả |
|---|---|
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Python 3.13.9) | **32 test, 32 pass, 0 fail** (`Ran 32 tests in 2.901s — OK`) |
| `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out <scratch>/out.jsonl` | mã 0; 62 dòng (snapshot tick 0, 10, …, 600 + `end`); không có event (người chơi đứng yên ở bến); `end.reason = "tick_limit"` |
| Chạy lại cùng lệnh ra `out2.jsonl`, `cmp` | **giống từng byte** |
| `--mode quan --seed 1 --ticks 0` | mã 0; snapshot + end, `stock:{}`, `customers:[]` |

Lưu ý: test hiện có **chỉ phủ khung** (CLI, bơi, mép, hết giờ, bến, kho). Chưa có test nào cho oxy/ngạt/hái/bắt cá/quán, nên xanh lúc này **không** nói gì về luật nhóm viết.

---

## 1. Bản đồ code: các `TODO(nhóm)`

| # | File:dòng (HEAD) | Hàm | Việc | Người (theo `docs/plan/phase-1.md:17-20`) |
|---|---|---|---|---|
| 1 | `chonoi/sim/gather.py:10-15` (docstring) | — | Mô tả lát 1: oxy, ngạt, Máu, ngất, dive/surface/oxygen_empty/choke/faint, giỏ LIFO | TV1 |
| 2 | `chonoi/sim/gather.py:112` | `GatherSim.step` (sau `_move`) | So vùng đầu/cuối bước → `dive` / `surface` (data: `pos`) | TV1 |
| 3 | `chonoi/sim/gather.py:113-114` | `GatherSim.step` | Oxy theo `d` cuối bước, `oxygen_empty`, đếm ngạt, `choke`, Máu 0 → `faint` + `gather_end("fainted")` giỏ rỗng, `return` | TV1 |
| 4 | `chonoi/sim/gather.py:16-19` (docstring) | — | Mô tả lát 2: hái, mọc lại, bắt cá, hồi chiêu, bến trước hái | TV2 |
| 5 | `chonoi/sim/gather.py:120-121` | `GatherSim.step` (nhánh `interact`, sau bến) | Chỉ ở mặt nước: hái nút `ready` gần nhất trong `interact_radius`, hòa thì id nhỏ; `gather` / `hold_full`; đặt `regrow_ticks` | TV2 |
| 6 | `chonoi/sim/gather.py:124` | `GatherSim.step` (nhánh `catch`) | Chỉ khi `catch_cd_ticks == 0` và dưới nước: `fish_caught` / `hold_full` | TV2 |
| 7 | `chonoi/sim/quan.py:4-5` (docstring) | — | Lát 3: khách theo lịch, chọn món nấu được, giữ chỗ, kiên nhẫn, `customer_left`, `no_dish` | TV3 |
| 8 | `chonoi/sim/quan.py:40` | `QuanSim.__init__` | Dựng khách từ scenario `customers[]`, suy ra `reserved` | TV3 |
| 9 | `chonoi/sim/quan.py:75` | `QuanSim.step` (trước `_move`) | Giảm kiên nhẫn / nấu / ăn; bếp chín → ready; xử lý khách theo PRD-0 mục F | TV3 (khách) + TV4 (bếp, ăn) |
| 10 | `chonoi/sim/quan.py:6-7` (docstring) | — | Lát 4: `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, boa, uy tín, `quan_end` | TV4 |
| 11 | `chonoi/sim/quan.py:77` | `QuanSim.step` (sau `_move`) | Tối đa MỘT interact/tick, chọn theo (khoảng cách, bếp trước bàn, id) | TV4 |
| 12 | `chonoi/sim/quan.py:78` | `QuanSim.step` | Khách mới theo `first_customer_tick`, `customer_interval_s`; `no_dish` | TV3 |
| 13 | `chonoi/scenario.py:4-5` | `_validate_quan` (`:143-163`) | Kiểm mâu thuẫn mức luật → mã 2 (giữ chỗ quá kho, đơn `assigned` phải đúng một món, khách `eating` thiếu giá/tip…) | TV3 |
| 14 | `chonoi/contract.py:139` | `validate_tuning` | (Tùy chọn) kiểm thêm khóa còn lại (bếp/bàn, uy tín…) | TV1 — **file khung, nhóm không sửa ở P1** |

Ghi chú: `scenario.py` và `contract.py` nằm trong danh sách "file khung" của luật chung (task này) nhưng TODO #13 lại giao cho nhóm. **CÂU HỎI cho team lead**: TV3 có được sửa `chonoi/scenario.py` không? (plan `:19` nói có.)

---

## 2. Test Contract headless

### 2.1 Lệnh và cờ (`chonoi/headless.py:34-81`)
```
python3 -m chonoi.headless --mode gather|quan --seed N --ticks N --out PATH
        [--scenario F] [--inputs F] [--inventory F (chỉ quan)] [--inventory-out F (chỉ gather)]
        [--snapshot-every N (mặc định 10)]
```
- `headless_cmd` đọc từ `game.contract.json:7`; test hộp đen gọi qua đó (`tests/helpers.py:23-32`).
- Mã thoát: **0** bình thường; **2** đầu vào sai, kiểm **trước khi ghi đầu ra** (`headless.py:46-71`, test `test_smoke_p1.py:58-68`); **1** lỗi ghi (`:78-80`). Lỗi mức luật lúc dựng sim (`BadInput` trong `__init__`) cũng → 2 (`:75-77`) và **không để lại file `--out`**: `runner.py:78` dựng `Session` (gọi `__init__` của sim) **trước** khi `runner.py:80` mở `JsonlWriter`. Đã thử: scenario quan có `stoves:[{"id":"B9",…}]` → `QuanSim._merge` ném `BadInput` (`quan.py:54-56`) → mã 2, không có file đầu ra. *(Bản trước của mục này ghi ngược lại, đã sửa theo phản biện của worker spec.)* Vì vậy kiểm mâu thuẫn mức luật đặt ở `scenario.py` hay trong `__init__` của sim đều an toàn. **Chỉ không an toàn** nếu `BadInput` ném trong `step()`: lúc đó file đã mở và đã ghi snapshot tick 0 (`runner.py:80-82`), `finally` đóng file nhưng không xóa → mã 2 mà vẫn còn file dở. Đừng ném `BadInput` trong `step()`.
- Mã 2 cho: `--mode day/river`, `--ticks < 0`, `--snapshot-every <= 0`, `--inventory` khác quan, `--inventory-out` khác gather, đường dẫn vào/ra trùng, vừa `quan.stock` vừa `--inventory`, contract ngoài dải (`contract.py`), inputs sai (`inputs.py:26-61`: tick trùng/giảm, nút lạ như `jump`/`attack`, move ngoài [-1,1]), scenario sai (`scenario.py`).

### 2.2 Inputs (`chonoi/inputs.py`)
- `{"frames":[{"tick":k, "move":[a,b], "interact":bool, "catch":bool}]}`; trường vắng **kế thừa** giá trị trước (`:79-91`).
- Bước k đọc frame có `tick == k` (`runner.py:85`); sự kiện của bước đó ghi **tick = k+1** (`runner.py:58-61`).
- `pressed()` = **cạnh lên** false→true; giữ `true` nhiều tick chỉ tính 1 lần (`test_python_starter_units.py:28-39`).
- `move` chuẩn hóa nếu độ dài > 1 (`inputs.py:64-69`) → bơi chéo không nhanh hơn.

### 2.3 Định dạng JSONL (`chonoi/runner.py`, `chonoi/jsonl.py`)
Thứ tự: snapshot tick 0 → mỗi bước: các event (theo thứ tự `step` trả) rồi snapshot nếu `tick % snapshot_every == 0` hoặc buổi kết thúc → snapshot cuối nếu chưa có → đúng 1 dòng `end` (`runner.py:77-97`). Tối đa 1 snapshot/tick.

- Số thực làm tròn **3 chữ số khi xuất**, không có `-0.0`; JSON `separators=(",", ":")`, `ensure_ascii=False` (`jsonl.py:6-18`). Tính toán bên trong dùng giá trị chính xác.
- **snapshot** chung (`runner.py:28-35`): `type, tick, sim_tick, mode, phase, phase_tick, state("playing"|"finished"), time_left_ticks, money, earned, reputation, score`, với `score = earned + reputation_multiplier × floor(reputation)`.
- **snapshot gather** (`gather.py:82-96`): `player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface}`, `hold` (mảng theo thứ tự nhặt, cuối = mới nhất), `hold_count`, `hold_capacity`, `nodes[{id,pos,kind,ready,regrow_ticks}]` sắp theo id, `fish[{id,pos,kind,heading_deg}]` sắp theo id.
- **snapshot quan** (`quan.py:60-70`): `player{pos}` (chưa có `vel`), `stock` (bỏ mục 0, sắp key), `hand`, `stoves[{id,pos,state,dish,cook_ticks_left,ready_ticks}]`, `tables[{id,pos,customer_id}]`, `customers` = **dict thô** sắp theo id (mọi trường trong dict đều lộ ra JSONL).
- **event**: `{"type":"event","tick":k+1,"phase":..,"name":..,"data":{..}}`.
- **end** (`runner.py:63-69`): `type, ticks, sim_tick, mode, state, reason (lý do sim hoặc "tick_limit"), money, earned, reputation, score`.

### 2.4 Danh sách sự kiện

| Sự kiện | Mode | `data` đã có trong code | Nguồn | Trạng thái |
|---|---|---|---|---|
| `node_regrown` | gather | `{node_id}` | `gather.py:105-109` | ĐÃ CÓ |
| `gather_end` | gather | `{reason: docked\|time\|fainted, inventory:{items:{..}}}` | `gather.py:137-140` | ĐÃ CÓ (`fainted` chưa) |
| `dive`, `surface` | gather | `{pos}` | `gather.py:112` | TODO; data theo comment |
| `oxygen_empty` | gather | ? | `gather.py:113` | TODO; **GIẢ ĐỊNH** `{}` hoặc `{pos}` |
| `choke` | gather | ? | `gather.py:12` | TODO; **GIẢ ĐỊNH** `{hp}` |
| `faint` | gather | ? | `gather.py:13` | TODO; **GIẢ ĐỊNH** `{pos}` |
| `gather` (hái) | gather | ? | `gather.py:17,121` | TODO; **GIẢ ĐỊNH** `{node_id, kind, count}` |
| `fish_caught` | gather | ? | `gather.py:18,124` | TODO; **GIẢ ĐỊNH** `{fish_id, kind, count}` |
| `hold_full` | gather | ? | `gather.py:17-18` | TODO; **GIẢ ĐỊNH** `{}` hoặc `{source_id}` |
| (khách đến) | quan | ? | `quan.py:4,78` | Tên chưa có trong starter; UI đoán `customer_arrived` (`chonoi/web/index.html`, bản đang sửa). **CÂU HỎI** PRD mục E |
| `customer_left`, `no_dish` | quan | ? | `quan.py:5` | TODO |
| `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | quan | ? | `quan.py:6-7` | TODO; UI đọc `data.dish_id` nếu có |
| `quan_end` | quan | `{reason:"time", money, earned, shift_earned, reputation}` | `quan.py:79-83` | ĐÃ CÓ |

Tên `data` các sự kiện TODO **không có nguồn** → phải chốt ở `docs/contracts/` (TV1). Test ẩn có thể so cả `data`; đây là rủi ro lớn nhất không giải được bằng code.

### 2.5 Schema kho (`chonoi/inventory.py`, `docs/contracts/inventory.sample.json`)
- `{"items": {id: số nguyên >= 0}}`, chỉ đúng một khóa gốc `items`; id thuộc `ca_loc, ca_linh, bong_dien_dien, bong_sung` (`inventory.py:13`). Sai → mã 2.
- Ghi: bỏ mục 0, sắp key, `{"items":{...}}` + `\n`, ghi nguyên tử qua file tạm (`inventory.py:49-61`).
- Ghi **đúng một lần, chỉ khi buổi kết thúc** (`gather_end`); dừng do `--ticks` thì **không tạo file** (`runner.py:71-74`, test `test_smoke_p1.py:221-228`).
- `gather_end.data.inventory` == nội dung file (test `test_smoke_p1.py:213-215`).
- Ngất: `inventory_items()` đọc `self.hold` (`gather.py:79-80`) → phải **xóa giỏ trước** `_finish("fainted")` để kho = `{"items":{}}`.

### 2.6 Tất định
- Cùng seed + cùng input → JSONL giống từng byte (`test_smoke_p1.py:48-56`). Đã kiểm tay: đạt.
- Ngẫu nhiên chỉ qua `Streams(seed).get(tên)` (`rng.py`); mỗi tên một luồng, không phụ thuộc thứ tự gọi. Đừng dùng `random`, `time`, `set` để duyệt (thứ tự set của chuỗi đổi theo `PYTHONHASHSEED`!), đừng duyệt `dict` dựng từ nguồn không cố định.
- Duyệt thực thể luôn qua `sort_by_id` (F2 trước F10, `ids.py:8-17`).

---

## 3. Bảng số liệu `game.contract.json`

`TICK = 60` (hard-code ở `gather.py:29`, `quan.py:13`; `tick_hz` trong contract không được đọc). Quy đổi giây → tick: `int(round(s*60))` như khung đang làm (`gather.py:48,55`).

### gather
| Khóa | Giá trị | Tick | Luật dùng | Đọc ở đâu |
|---|---|---|---|---|
| `duration_s` | 180 | 10800 | hết giờ → `gather_end time` | `gather.py:55`, `scenario.py:54` |
| `bounds` | x[0,100], d[0,30] | | chặn mép, vel về 0 | `gather.py:148-157` |
| `dock_pos`, `dock_radius` | [2,0], 3 | | `interact` khi `dist ≤ 3` → `docked` | `gather.py:134-135` |
| `start_pos`, `start_heading_deg` | [2,0], 0 | | vị trí đầu (đang ở trong bến!) | `gather.py:43,47` |
| `swim_speed` | 4.0 | 0.0667/tick | bơi | `gather.py:143` |
| `ramp_max_ticks` | 6 | | tăng/giảm tốc | `gather.py:145`, `ramp.py` |
| `surface_depth` | 0.5 | | mặt nước khi `d ≤ 0.5` | `gather.py:131-132` |
| `oxygen_max_s` | 30 | 1800 | oxy tối đa | `gather.py:48` |
| `oxygen_refill_per_tick` | 6 | | hồi ở mặt nước (0→đầy: 300 tick) | **TODO lát 1** |
| `choke_interval_ticks` | 60 | | ngạt −1 Máu | **TODO lát 1** (scenario hard-code 59, `scenario.py:121`) |
| `hp_max` | 3 | | Máu; 0 → ngất | `gather.py:50,86` |
| `hold_capacity` | 12 | | sức chứa giỏ | `gather.py:90` |
| `interact_radius` | 2.0 | | bán kính hái | **TODO lát 2** |
| `node_yield` | 1 | | số món mỗi lần hái | **TODO lát 2** |
| `regrow_s` | 20 | 1200 | `regrow_ticks` sau khi hái | **TODO lát 2** (đếm ngược đã có `gather.py:105-109`) |
| `catch_radius` | 2.0 | | bán kính bắt cá | **TODO lát 2** |
| `catch_cooldown_s` | 0.5 | 30 | hồi chiêu `catch_cd_ticks` | **TODO lát 2** (giảm đã có `gather.py:104`) |
| `fish_yield` | ca_linh 3, ca_loc 1 | | số món mỗi lần bắt | **TODO lát 2** |
| `nodes` | N1,N2 điên điển (x12,28); N3,N4 bông súng (x44,60); d=0 | | | `gather.py:57-59` |
| `fish_initial` | F1..F6 (linh/lóc xen kẽ, d 5–16) | | đứng yên ở P1 (`gather.py:66`) | `gather.py:60-68` |

### quan
| Khóa | Giá trị | Tick | Luật dùng | Đọc ở đâu |
|---|---|---|---|---|
| `duration_s` | 180 | 10800 | `quan_end time` | `quan.py:34` |
| `bounds` | x[0,16], z[0,10] | | chặn mép | `quan.py:90` |
| `start_pos` | [8,5] | | | `quan.py:27` |
| `walk_speed`, `ramp_max_ticks` | 4.0, 6 | | đi | `quan.py:87-89` |
| `interact_radius` | 1.5 | | interact bếp/bàn | **TODO lát 4** |
| `stoves` | B1 [2,8] | | | `quan.py:36-38` |
| `tables` | T1 [9,2] | | 1 bàn → 1 khách cùng lúc | `quan.py:39` |
| `first_customer_tick` | 120 | 120 | khách đầu | **TODO lát 3** |
| `customer_interval_s` | 15 | 900 | khách sau: 120, 1020, 1920, … | **TODO lát 3** |
| `patience_s` | 60 | 3600 | kiên nhẫn → `customer_left` | **TODO lát 3** |
| `eat_s` | 10 | 600 | ăn xong → `paid` | **TODO lát 4** |
| `burn_s` | null | | bắt buộc null ở P1 (`contract.py:137-138`) | — |
| `carry_limit` | 1 | | bưng tối đa 1 món (`hand`) | **TODO lát 4** |
| `tip_rate` | 0.2 | | boa = 20% giá | **TODO lát 4** |
| `tip_min_patience_ratio` | 0.5 | 1800 | boa khi kiên nhẫn còn ≥ 50% | **TODO lát 4** |
| `tip_reputation` | 0.2 | | +uy tín khi có boa | **TODO lát 4** |
| `left_reputation_delta` | −0.5 | | uy tín khi khách bỏ đi | **TODO lát 3** |
| `reputation_initial` | 3.0 | | | `quan.py:35`, `gather.py:74` |
| `reputation_min/max` | 0 / 5 | | kẹp uy tín | **TODO** |
| `score.reputation_multiplier` | 100 | | `score` | `runner.py:29-34` |

### menu
| Món | Công thức | cook_s (tick) | Giá | Boa 20% |
|---|---|---|---|---|
| `ca_loc_nuong_trui` | ca_loc 1 | 6 (360) | 60 | 12 |
| `goi_bong_sung` | bong_sung 2 | 4 (240) | 40 | 8 |
| `lau_ca_linh_dien_dien` | ca_linh 3 + bong_dien_dien 1 | 10 (600) | 120 | 24 |

Boa với menu mặc định luôn là số nguyên → câu hỏi làm tròn (clarify #10) **không ảnh hưởng output** với contract hiện tại; contract chỉ đọc từ file trong repo (`contract.py:8`), test không đổi được tuning. Vẫn nên chốt (GIẢ ĐỊNH: `round()` hoặc `int()`), ghi vào contracts.

---

## 4. Edge case & thứ tự trong một tick

### 4.1 Thứ tự bước gather (khung `gather.py:99-128`)
1. `time_left_ticks−1`, `invuln−1`, `catch_cd−1`, đếm ngược nút → `node_regrown` (theo id).
2. `_move` (bơi + chặn mép).
3. *(TODO lát 1)* `dive`/`surface` → oxy → `oxygen_empty` → đếm ngạt → `choke` → Máu 0: `faint`, xóa giỏ, `gather_end(fainted)`, **return**.
4. `interact` (cạnh lên): **bến trước** → `gather_end(docked)`, return; nếu không: hái (chỉ mặt nước).
5. `catch` (cạnh lên): chỉ khi `catch_cd_ticks == 0` và dưới nước.
6. `time_left_ticks <= 0` → `gather_end(time)`.

Hệ quả cần giữ: ngất thắng hết giờ cùng tick; bến thắng hết giờ cùng tick (return sớm); hái/bắt cá ở tick cuối vẫn vào kho.

### 4.2 Bảng edge case

| Edge case | Code/test đã ngầm trả lời? | Khuyến nghị |
|---|---|---|
| Oxy theo `d` đầu hay cuối bước (clarify #3) | **Có**: comment `gather.py:113` "oxy theo d CUỐI bước"; `_at_surface` dùng `d ≤ surface_depth` (`gather.py:131-132`); scenario dùng `pos[1] > surface_depth` là dưới nước (`scenario.py:123,137`) | Làm theo: sau `_move`, dùng `_at_surface()` |
| `oxygen_empty` phát khi nào | **Có**: "khi từ dương xuống 0" (`gather.py:113`) → scenario bắt đầu với `oxygen_ticks:0` thì **không** phát | Chỉ phát ở chuyển tiếp >0 → 0 |
| Ngạt: chu kỳ, reset (clarify #4) | **Một phần**: `zero_oxy_ticks` hợp lệ trong `[0, 59]` (`scenario.py:121-122`) → khi đạt 60 thì `choke` và đếm lại về 0; `zero_oxy_ticks > 0` chỉ khi oxy 0 **và dưới nước** (`scenario.py:123-124`) → lên mặt nước (oxy hồi > 0) bộ đếm về 0 | Đủ `choke_interval_ticks` → −1 Máu, `zero_oxy_ticks = 0` |
| Tick oxy chạm 0 có tính là tick ngạt #1? | **Không** | **CÂU HỎI**. Lệch 1 tick choke/faint (vd. từ oxy đầy dưới nước: choke ở tick 1859 hay 1860). Fixture kiểu `oxygen_ticks:0, zero_oxy_ticks:59` cho kết quả như nhau ở cả hai cách. GIẢ ĐỊNH đề xuất: đếm ngay sau khi cập nhật oxy, nếu oxy==0 và dưới nước thì +1 (gồm tick chạm 0) — đúng nghĩa đen comment `gather.py:12` |
| Ngất: kho (clarify #2) | **Có**: docstring `gather.py:13` "mất toàn bộ giỏ, kho rỗng"; comment `:114` "giỏ rỗng" | Xóa `hold` rồi `_finish("fainted")` → kho `{"items":{}}` (file vẫn được ghi) |
| Thứ tự event lúc ngất | Một phần: `:114` "faint + gather_end" | `choke` → `faint` → `gather_end` cùng tick |
| Hết giờ giữ giỏ (clarify #1) | **Có, có test**: `test_smoke_p1.py:182-197` (time_left 3 → `gather_end` tick 3, kho giữ `ca_loc`) | Đừng đổi |
| Bến khi đang dưới nước | Khung cho phép: `_in_dock` chỉ xét `dist ≤ 3` (`gather.py:134-135`), đã thử: `pos [2,2.5]` + interact → `docked` | **CÂU HỎI**: PRD có yêu cầu ở mặt nước không? Hiện code khung = được |
| Bến xét trước hái | **Có**: `gather.py:115-119`, comment `:19` | Giữ |
| Hái chỉ ở mặt nước | **Có**: comment `gather.py:120` | Dùng `_at_surface()` |
| Hái: nút `ready` gần nhất, hòa id nhỏ (clarify #7) | **Có**: `gather.py:120-121` | `min(…, key=(dist, id_key))` trên nút `regrow_ticks == 0` trong `interact_radius` (≤, cùng kiểu so với bến) |
| Bắt cá: chọn đàn nào | Không ghi rõ | GIẢ ĐỊNH: gần nhất trong `catch_radius`, hòa id nhỏ (như hái) |
| Hồi chiêu bắt cá | **Một phần**: chỉ khi `catch_cd_ticks == 0` (`gather.py:124`); giảm ở bước 1 (`:104`) | Đặt `catch_cd = 30` khi bắt được → bắt lại sau 30 tick. **CÂU HỎI**: bấm hụt (không có cá) / `hold_full` có tính hồi chiêu không? |
| Giỏ đầy một phần (clarify #5) | **Gợi ý**: contract buộc `fish_yield ≤ hold_capacity` (`contract.py:79-80`) — chỉ có nghĩa nếu bắt là "tất cả hoặc không" | **CÂU HỎI**. GIẢ ĐỊNH: không đủ chỗ cho cả mẻ → `hold_full`, không nhặt, cá không mất |
| Cá biến mất sau khi bắt (clarify #6) | Không. Khung: "Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau" (`gather.py:66`); `IdAllocator.reserve` cho cả cá (`:69-71`) gợi ý phase sau cấp id cá mới | **CÂU HỎI** |
| LIFO | **Có**: `hold` là mảng, "cuối mảng là mới nhất" (`gather.py:54`); kho đếm, sắp theo id (`inventory.py:41-46`) | `append` theo thứ tự nhặt; một mẻ 3 cá linh = 3 phần tử. LIFO ở P1 chỉ lộ qua thứ tự `hold` trong snapshot |
| `node_regrown` cùng tick với hái | Đếm ngược ở bước 1, hái ở bước 4 → nút về 0 tick k thì hái được ngay tick k | Đặt `regrow_ticks = 1200` lúc hái; `node_regrown` phát sau 1200 bước |
| `dive`/`surface` | `:112` "so phân vùng đầu/cuối bước", data `pos` | Lưu `was_surface` trước `_move`; phát trước oxy |
| Quán: một interact/tick, ưu tiên | **Có**: `quan.py:77` (khoảng cách, bếp trước bàn, id) | key `(dist, 0 nếu bếp / 1 nếu bàn, id_key)` trong `interact_radius` |
| Quán: lịch khách | `quan.py:78`; không có bộ đếm tick trong `QuanSim` | Cần thêm `elapsed`. **CÂU HỎI**: khi scenario đặt `time_left_ticks`, lịch tính theo tick từ đầu lượt chạy hay `duration − time_left`? |
| Khách đến lúc bàn có người (clarify #9) | Scenario cấm 2 khách cùng bàn (`scenario.py:162-163`) | **CÂU HỎI**. Mặc định chỉ 1 bàn nên sẽ gặp ngay ở khách #2 (tick 1020) nếu khách #1 chưa đi |
| Chọn món (clarify #8) | Không. `Streams` có sẵn | **CÂU HỎI**. Nếu dùng RNG: tên luồng riêng (vd. `"customer_dish"`), duyệt menu theo id đã sắp |
| Giữ chỗ nguyên liệu | `customers[].reserved` (`quan.py:41`); scenario.py TODO "khách giữ chỗ quá kho" | Món "nấu được" = `stock − Σreserved` đủ công thức; không đủ → `no_dish` |
| Trạng thái khách | Gợi ý `assigned`, `eating` (`scenario.py:4-5`), UI đọc `state`, `dish_id`, `patience_ticks_left`, `table_id` | Chốt trường trong contracts |
| Boa / kiên nhẫn ≥ 50% (clarify #10) | Không | GIẢ ĐỊNH: so `patience_ticks_left / patience_ticks ≥ 0.5` lúc `served` |
| Uy tín kẹp [0,5] | Không | Kẹp sau mỗi thay đổi; `score` dùng `floor(reputation)`. Sai số float có thật (3.0+0.2×5 = 4.000000000000001) nhưng đã thử mọi chuỗi ±0.2/−0.5 dài ≤ 8 từ 3.0: `floor` không lệch. Vẫn nên làm tròn uy tín (vd. `round(x, 6)`) sau mỗi cộng/trừ cho chắc |
| `--ticks 0` | Có test (`test_smoke_p1.py:24-33`) | — |

---

## 5. Snapshot UI đọc từ `chonoi/live.py`

`GET /state` = `Session.snapshot()` (như dòng snapshot headless) **+** `meta` (= `tuning[mode]`, **không có `menu`**), `events` (40 event gần nhất), `finished`, `reason`, `error` (`live.py:101-109`). `POST /input` `{move, interact, catch}`; `POST /restart`.

| Trường | Có trong snapshot? | UI dùng (`chonoi/web/index.html`) |
|---|---|---|
| `tick, mode, time_left_ticks, money, reputation, score` | có | đồng hồ, tiền, uy tín, điểm |
| `earned` | có | chưa hiển thị |
| `player.pos/heading_deg/oxygen_ticks/oxygen_max_ticks/hp/hp_max/invuln_ticks/catch_cd_ticks/at_surface` (gather) | có | thanh oxy, tim, nhấp nháy, vòng bán kính |
| `player.zero_oxy_ticks` | có | chưa dùng → gợi ý: cảnh báo "sắp ngạt" (đếm tới 60) |
| `hold, hold_capacity` | có | ô giỏ, đánh dấu món trên cùng |
| `nodes[].ready/regrow_ticks`, `fish[]` | có | vẽ |
| `stoves[].state/dish/cook_ticks_left` | có (khung) | màu bếp, đếm giờ |
| `stoves[].ready_ticks` | có | chưa dùng |
| `tables[].customer_id` | có | |
| `customers[].state/dish_id/patience_ticks_left/table_id` | **chưa** — khung chỉ đổ dict thô, nhóm (TV3) phải thêm | màu khách, tên món, thanh kiên nhẫn |
| `customers[].eat_ticks_left` (tên GIẢ ĐỊNH) | chưa | gợi ý thanh "đang ăn" |
| `hand` | có (`null`); dạng chuỗi hay object chưa chốt — UI xử lý cả hai | |
| `stock` | có | |
| `player.vel` (quan) | **chưa** (gather có) | không cần cho UI; nên thêm cho đồng nhất |
| `shift_earned` | chỉ trong event `quan_end` | thiếu nếu HUD muốn hiện tiền ca |
| Menu (giá, công thức, cook_s) | **không** (`meta` chỉ là `tuning.quan`) | HUD quán thiếu bảng menu → UI hard-code (`DISH_NAME`) hoặc đề xuất `live.py` thêm `meta_menu` (file khung — cần team lead đồng ý) |
| Đếm ngược khách kế tiếp | không | gợi ý nhóm thêm vào snapshot quan (vd. `next_customer_ticks`, GIẢ ĐỊNH) |

Lưu ý: UI đang hard-code tên event quán (`customer_arrived`, …) — phải khớp tên TV3/TV4 chốt.

---

## 6. Rủi ro & khuyến nghị cho test ẩn

1. **Tên/`data` sự kiện chưa chốt** (mục 2.4) — rủi ro lớn nhất. TV1 ghi danh sách vào `docs/contracts/` trước khi code; PO hỏi PRD mục E.
2. **Lệch 1 tick** ở ngạt/hồi chiêu/mọc lại/lịch khách. Dùng quy ước "giảm bộ đếm ở bước 1, kích hoạt khi về 0 / đạt ngưỡng" như khung; viết unit test cho đúng tick bằng fixture scenario (`oxygen_ticks`, `zero_oxy_ticks`, `catch_cd_ticks`, `regrow_ticks`, `time_left_ticks`).
3. **Ngất phải xóa giỏ trước `_finish`** — nếu không kho ghi sai.
4. **`customers` lộ dict thô** (`quan.py:69`): trường lạ từ scenario đi thẳng ra JSONL (đã thử: `"foo":1` hiện trong snapshot). Nên dựng khách với tập trường cố định và sắp khóa cố định; không để bộ đếm nội bộ/`set` trong dict.
5. **Kiểm mâu thuẫn trước vòng tick** — ở `scenario.py` hoặc `__init__` của sim đều được, vì `Session` được dựng trước khi mở file (`runner.py:78-80`, đã thử). Không ném `BadInput` trong `step()`, vì lúc đó file `--out` đã được ghi một phần mà mã thoát vẫn là 2.
6. **Float & `floor(reputation)`** — rủi ro thấp (mục 4.2), làm tròn uy tín cho chắc.
7. **Không dùng `set`/`random`/đồng hồ**; luôn `sort_by_id`. RNG đặt tên luồng riêng để phase sau thêm luồng không làm lệch P1.
8. **Kiểm lại phase trước**: test ẩn phase 2–4 chạy lại kịch bản P1. Mọi tính năng/sáng tạo mới phải tắt ở headless hoặc không đổi chuỗi event P1 (ví dụ cá bơi, sinh vật). Giữ `--mode day` trả mã 2 tới khi phase yêu cầu. Nên lưu file JSONL vàng (golden) của vài kịch bản P1 vào `tests/` và so byte ở mọi phase.
9. **Kết thúc bằng `interact` ở tick 0**: start_pos nằm trong bến → bấm E ngay là `docked`. Test hái phải đặt `player.pos` ra khỏi bến (scenario).
10. `team_size` đang là **4** (`game.contract.json:4`) trong khi `TEAM.md` ghi 6 người → `tools/check_team.py` báo lỗi; TV1 sửa.
11. Snapshot quan tick 0: `player.pos` là `[8,5]` (int) trong khi gather là `[2.0,0.0]` (`quan.py:27` không ép float). So giá trị JSON thì bằng, so chuỗi thì khác — vô hại nếu test ẩn so giá trị; nếu sửa thì sửa ở `quan.py` (vùng nhóm).

## 7. Câu hỏi mở (đề xuất PO đưa vào `docs/clarify.md`)
- Q-A: Tick oxy chạm 0 có tính là tick ngạt đầu tiên không?
- Q-B: Bấm `catch` hụt / gặp `hold_full` có bắt đầu hồi chiêu không?
- Q-C: Cập bến có cần ở mặt nước không (khung hiện cho phép dưới nước trong bán kính 3)?
- Q-D: Tên + `data` của mọi sự kiện gather/quan (PRD mục E).
- Q-E: Lịch khách tính theo tick nào khi scenario đặt `time_left_ticks`?
- Q-F: TV3 có được sửa `chonoi/scenario.py` (file khung) cho TODO kiểm mâu thuẫn không?
- Giữ nguyên các câu `CHỜ HỎI` #4, #5, #6, #8, #9, #10 trong `docs/clarify.md`; #1, #2, #3, #7 đã có căn cứ trong code (mục 4.2).
