# Research Phase 3 — Contract v1.2: kho cá thể + độ tươi

> Người viết: agent RESEARCH (Claude) cho TV6, chỉ đọc code. Ngày 2026-11-21, branch `tv6/phase-1-team-ai`, HEAD `80c017e` (đã gồm merge PR #1 `QuanSim`).
> Nguồn: `docs/prd/phase-3-ticket-03.md` (TICKET-03, 140 dòng, có dòng lặp), brief `.lab-notes/brief-phase-2-3.html`, ADR `docs/adr/0001-kho-ca-the-v1-2.md`.
> Số dòng `chonoi/` theo HEAD. Chỗ suy luận ghi **GIẢ ĐỊNH**.

## 0. Hiện trạng (đo lúc viết)

| Mục | Trạng thái |
|---|---|
| Test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → **32 test, OK** |
| `game.contract.json` | vẫn **v1.0** (`"contract_version": "1.0"`, `team_size: 4`, 6 cá dạng mảng). JSON v1.1 trong `docs/research/phase-2.md` **chưa được dán** |
| Gather | Lát 1 có (oxy, ngạt, ngất, `try_add_hold`). Hái và bắt cá vẫn TODO (`gather.py:120,124`). Chưa có cá bơi, Cá Sấu (P2) |
| Quán | PR #1 thêm 4 hàm thao tác (`start_cooking` `quan.py:73-93`, `finish_cooking` `:95-100`, `pick_dish` `:102-108`, `serve_dish` `:110-120`) nhưng **chưa nối vào `step()`** (`:122-134` vẫn TODO). Chưa có khách, giữ chỗ, tiền |
| Mode `day`, Shop, pause | chưa có (`headless.py:47-48` vẫn chặn `day`) |
| Tag | chưa có tag nào |

Hệ quả: v1.2 nằm **trên** v1.1. Thứ tự thực tế: P1 lõi → v1.1 (số chuẩn) → adapter v1.2. Bật `"1.2"` khi gather chưa có id cá thể sẽ làm mọi test dùng `hold` vỡ (mục 5).

---

## 1. Diff contract v1.1 → v1.2

| Khóa | v1.1 | v1.2 | Nguồn |
|---|---|---|---|
| `contract_version` | `"1.1"` | **`"1.2"`** | đề `:42` |
| `freshness` | — | `{"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}` | đề `:42` |
| Schema kho | đếm `{"items":{kind:n}}` | mảng cá thể `{"items":[{id,kind,fresh}]}` (không phải khóa tuning, nhưng đổi theo `contract_version`) | đề `:11-14` |
| Mở rộng (chỉ khi làm) | — | `gather.current {interval_ticks, duration_ticks, warning_ticks, min_depth, speed}`; `reservations {count, table_hold_s, price_multiplier, failed_reputation_delta}` = 2, 30, 1.5, −1 | đề `:72`, `:96` |

Không khóa số nào của v1.1 bị đổi. GIẢ ĐỊNH: `freshness` đặt trong `tuning` (cạnh `gather`, `quan`, `menu`), như `shop`/`day_plan` ở v1.1.

### JSON đề xuất để TV1 dán
Áp lên JSON v1.1 ở `docs/research/phase-2.md` mục 1.4 (dán v1.1 trước nếu chưa làm):

```json
{
  "contract_version": "1.2",
  "tuning": {
    "freshness": {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
  }
}
```
(chỉ là phần thay đổi: đổi `contract_version`, thêm khóa `tuning.freshness`; giữ nguyên các khóa khác.)

Quy đổi sang số nguyên (đề `:37`), dùng 240 đơn vị cho mỗi điểm tươi:

| Khóa | Giá trị | Đơn vị/tick | Công thức |
|---|---|---|---|
| `initial` | 100 | 24000 đơn vị | 100 × 240 |
| `gather_decay_per_s` | 0.5 | **2** | 0.5 × 240 / 60 |
| `quan_decay_per_s` | 0.25 | **1** | 0.25 × 240 / 60 |
| `spoiled_below` | 30 | 7200 đơn vị | ươn khi `units < 7200` |

Nên để `contract.py` kiểm `decay × 240 / 60` là số nguyên, nếu không thì báo mã 2, để giữ phép tính chính xác.

---

## 2. Schema kho cá thể

### 2.1 Quy tắc (đề `:11-15`, `:44`)
- File có **đúng một khóa gốc** `items`; giá trị là **mảng** `{id, kind, fresh}`. Kho rỗng: `{"items":[]}`.
- `id`: chuỗi khác rỗng, **duy nhất**. `kind` thuộc danh mục nguyên liệu (6 loại ở v1.1+). `fresh`: số **hữu hạn** trong `[0, 100]`.
- Mã 2 khi chạy v1.2 nếu: file kho **đếm** (items là object), sai schema, kind lạ, id trùng, fresh ngoài miền hoặc không hữu hạn (NaN/Infinity, `bool`).
- Bên đọc chọn schema theo `contract_version`.
- Kho quán nhận **nguyên** số lượng, id và fresh, **kể cả hàng ươn**. Sức chứa chỉ áp lên giỏ, không áp lên kho.
- **Cấp id**: `I1, I2, …` theo thứ tự vào giỏ, **tăng mãi** xuyên pha và Ngày, kể cả khi cá thể cũ đã dùng hoặc bỏ. Dùng `IdAllocator` (`ids.py:20-35`): `reserve()` mọi id có sẵn (scenario/kho), rồi `new("I")`.
- Trong `day`: Ngày đầu giữ nguyên id trong mẫu `gather.hold`; các Ngày sau cấp id mới cho mẫu theo thứ tự mảng, với kind/fresh ban đầu. Hàng mua ở Chợ (mở rộng) nhập riêng, `fresh: 100`, id mới.
- **Ghi**: đúng một lần khi có `gather_end`, qua file tạm cùng thư mục rồi thay thế nguyên tử. **Ngất ghi `{"items":[]}`**. Chạm `--ticks` trước `gather_end` thì không đụng tới file đích. Xuất **theo id** (thứ tự `sort_by_id`), đủ chính xác để đọc lại vẫn giữ giá trị và nhánh ở ngưỡng 30.
- `gather_end.data.inventory` dùng cùng schema.
- Scenario: `gather.hold` và `quan.stock` là mảng cá thể; `customers[].reserved` là **mảng id**. Id vật lý duy nhất giữa mọi nơi chứa (giỏ, kho, phần giữ). Phần giữ phải trỏ tới cá thể chưa ươn, đủ công thức, không dùng chung giữa các đơn. Đơn `reserved` mà bỏ trống `reserved` thì tự cấp theo `order_tick` rồi id bàn, lấy cá thể tươi nhất rồi id nhỏ. Sai → mã 2.

### 2.2 So với code hiện tại: chỗ phải đổi

| File:dòng | Hiện tại | Phải đổi (v1.2) | Loại file |
|---|---|---|---|
| `chonoi/inventory.py:13` `KINDS_P1` | 4 loại | 6 loại (thêm `ca_keo`, `keo_neo` từ v1.1) | khung (TV1) |
| `inventory.py:16-27` `validate_items` | object `{kind: int ≥ 0}`, bỏ mục 0 | thêm `validate_items_v12(list)`: mảng, mỗi phần tử đúng 3 khóa, id chuỗi khác rỗng duy nhất, kind hợp lệ, `fresh` là số (không phải bool), `math.isfinite`, trong [0,100] | khung |
| `inventory.py:30-38` `read_inventory` | luôn đọc schema đếm | thêm tham số `version`; `"1.2"`: items là object → `BadInput` (mã 2) | khung |
| `inventory.py:41-46` `hold_to_items` | giỏ là mảng kind → đếm | bỏ ở v1.2: giỏ là mảng cá thể, xuất `sort_by_id`, fresh = `units/240` | khung |
| `inventory.py:49-61` `write_inventory` | ghi `{"items":{…}}`, sắp key, lọc > 0; **đã nguyên tử** (`mkstemp` + `os.replace`) | ghi `{"items":[…]}` theo id; giữ cơ chế nguyên tử; **không** đi qua `jsonl._clean` (làm tròn 3 chữ số, `jsonl.py:6-13`) | khung |
| `chonoi/runner.py:71-74` `write_inventory_if_done` | ghi một lần khi `done`; không ghi khi dừng do `--ticks` | giữ logic, đã đúng đề. Ngất: `inventory_items()` phải trả `[]` | khung |
| `chonoi/headless.py:66` | `read_inventory(a.inventory)` | truyền `contract["contract_version"]` | khung |
| `chonoi/live.py:233` | như trên | như trên | khung |
| `chonoi/scenario.py:92-97` | `hold` là mảng kind | mảng cá thể (dùng chung validator v1.2) + kiểm sức chứa | khung |
| `scenario.py:147-148` | `stock` qua `validate_items` (object) | mảng cá thể; kiểm id duy nhất giữa `hold`, `stock`, `reserved` | khung |
| `scenario.py:157-163` | khách chỉ kiểm `table_id` | `reserved` là mảng id trỏ vào `stock`, chưa ươn, không trùng giữa đơn, đủ công thức | khung (hoặc kiểm trong `QuanSim.__init__`, như clarify #28) |
| `chonoi/contract.py:112-143` | không kiểm `freshness`, không kiểm version | kiểm `freshness` (4 khóa, decay chia hết như mục 1) và `contract_version ∈ {"1.0","1.1","1.2"}` | khung (TV1) |
| `chonoi/sim/gather.py:54` | `self.hold = list(scenario.get("hold", []))` (chuỗi) | mảng cá thể `{id, kind, units}`; `ids.reserve(id)` | TV2 |
| `gather.py:79-80` `inventory_items` | `hold_to_items` | mảng cá thể theo id | TV2 |
| `gather.py:89` snapshot `hold` | mảng kind | mảng `{id, kind, fresh}` (thứ tự vào giỏ) | TV2 |
| `gather.py:131-140` `try_add_hold(kind)` | `append(kind)` | cấp `I<n>` bằng `self.ids.new("I")`, `fresh = 100`, append | TV1/TV2 |
| `gather.py:163-166` ngất | `hold.clear()`, `faint {}` | bỏ phần còn lại **theo LIFO** (đảo mảng), `faint.data.lost` = mảng cá thể theo thứ tự bỏ (+ `hp:0` theo v1.1) | TV1 |
| `gather.py:99-109` đầu bước | đồng hồ, cooldown, hồi nút | thêm hao tươi hàng có sẵn −2 đơn vị/tick, phát `spoiled` theo id | TV2 |
| `chonoi/sim/quan.py:31` | `self.stock = dict(...)` (đếm) | mảng/dict cá thể theo id; `ids.reserve` | TV3/TV4 |
| `quan.py:40` | `reserved = c.get("reserved", {})` | mảng id | TV3 |
| `quan.py:63` snapshot `stock` | object đếm | mảng cá thể theo id | TV4 |
| `quan.py:73-93` `start_cooking` | kiểm và trừ theo **số lượng** loại | tiêu **đúng các id đang giữ**; chốt `base_price`; `cook_started.data.items` | TV4 |

---

## 3. Bảng tác động (mẫu ghi tác động của đề `:113-122`, theo code hiện tại)

| Module | File : hàm (HEAD) | Test bị ảnh hưởng: giữ / đổi / thêm | Người (brief) |
|---|---|---|---|
| **Adapter / schema** (làm trước) | `inventory.py`: `KINDS_P1` `:13`, `validate_items` `:16`, `read_inventory` `:30`, `hold_to_items` `:41`, `write_inventory` `:49`; `contract.py`: `validate_tuning` `:112`; `scenario.py`: `_validate_gather` `:84` (hold), `_validate_quan` `:143` (stock, reserved); `headless.py:66`; `live.py:233`; `game.contract.json` | **Đổi**: `test_smoke_p1.py:197,212,215,219,232-235,239-241,246` (mục 5). **Thêm**: kho đếm → mã 2; id trùng, kind lạ, fresh −1/100.5/NaN → mã 2; `{"items":[]}` hợp lệ; ghi nguyên tử, không để `.inv-*.tmp`; ngất ghi `[]`; `--ticks` cắt trước thì không có file | TV1 + agent khung (TV6) |
| **Lặn** | `gather.py`: `__init__` `:54`, `step` `:99-128` (bước 1), `try_add_hold` `:131`, `_oxygen_and_breath` `:145` (ngất), `inventory_items` `:79`, `snapshot` `:82`; sau này `_monster_hit` (P2) | **Đổi**: `test_python_starter_units.py:65` (hold chuỗi), `test_smoke_p1.py:85,184,204`. **Thêm**: scenario mẫu → `spoiled` tick 1; hàng mới không hao trong bước nhặt; 8400 vs 8401 bước (mục 4.3); id I tăng liên tục; `lost` LIFO | TV2 (+TV1) |
| **Quán** | `quan.py`: `__init__` `:31,40`, `snapshot` `:59-69`, `start_cooking` `:73-93`, `step` `:122` (hao tươi, spoiled, giữ lại, thứ tự tick) | **Thêm**: hao 1 đơn vị/tick kể cả hàng đang giữ; phần giữ vừa ươn → nhả, giữ lại một lần, thiếu → `unfulfillable`; `base_price` floor; boa trên giá đã chốt; `cook_started.items` sắp kind→id. **Đổi**: test giá/boa P1–P2 (chưa có trong repo) | TV3 (giữ chỗ) + TV4 (hao, giá, nấu) |
| **day** | `runner.py` (`Session`, `build_sim` `:21`), `sim/day.py` (chưa có) | **Thêm**: bàn giao cùng tick, không hao thêm; id tăng xuyên Ngày; Ngày 2 cấp id mới cho mẫu `gather.hold` | agent khung (TV6) |
| **HUD** | `chonoi/web/index.html` (giỏ, kho quán, Shop) | **Giữ**: `tests/test_live.py:41` (`player.pos`). Hiện số/thanh fresh, nhãn ươn (`fresh < 30`) | Cursor (TV6) |
| **QA** | `tests/`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `CHANGELOG.md` | **Giữ**: con_01/02/03, Movement, team, live. Regression P1–P2 còn hiệu lực; smoke bàn giao của đề (`:54`) | TV5 |

Thứ tự tích hợp đề xuất (khớp ADR-0001): (1) adapter đọc/ghi **cả hai** schema theo version, contract `freshness` → (2) Lặn, Quán, HUD song song → (3) day → (4) đổi `"1.2"`, sửa test mục 5 cùng commit, smoke, regression, `CHANGELOG.md`.

---

## 4. Thứ tự tick, sự kiện, số học

### 4.1 Thứ tự trong tick (đề `:39-40`)
**Gather**
1. Đồng hồ, cooldown, hồi nút (`node_regrown`), **hao tươi hàng có sẵn** (−2 đơn vị) → `spoiled` theo id.
2. (Lịch dòng lũ, nếu bật.)
3. Bơi → oxy → ngạt.
4. (Lao) → thủy quái / hit (rơi hàng LIFO).
5. Bến trước hái.
6. Bắt cá → (ảnh).
7. Hết giờ; nếu còn giờ: cá bơi, sinh thêm.
- Ngất: bỏ toàn bộ phần còn lại theo LIFO → `faint` → `gather_end(fainted)`.
- GIẢ ĐỊNH: trong bước 1, `node_regrown` phát trước `spoiled` (theo thứ tự liệt kê trong đề) → **câu hỏi Q3**.

**Quán**
1. Đồng hồ và timer.
2. Hao tươi kho thô (−1 đơn vị, kể cả hàng đang giữ) → phát **hết** `spoiled` theo id → rồi mới xử lý các phần giữ bị ươn (theo `order_tick` rồi id bàn: nhả toàn bộ, giữ lại đúng một lần, thiếu → `unfulfillable`, khách chờ tới hạn).
3. Món chín / cháy (nếu bật) theo id bếp.
4. Di chuyển và tối đa một tương tác.
5. Thanh toán, kiên nhẫn, đóng ca.
6. Nếu còn giờ: đặt trước (nếu bật) → khách thường.
- Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ. Giao đúng tick kết thúc ca thì được trả tiền ngay.

So với code: `QuanSim.step` (`quan.py:122-134`) mới có đồng hồ → di chuyển → hết giờ. Cần chèn bước 2–3 trước `_move` và bước 5–6 sau.

### 4.2 Sự kiện và dữ liệu mới/đổi (đề `:45-50`)

| Sự kiện | Data v1.2 | Ghi chú |
|---|---|---|
| `spoiled` (mới) | `{item_id, kind, location: "hold"\|"stock"}` | đúng một lần khi đi từ ≥ 30 xuống < 30; nhiều cá thể cùng tick → theo id. Ví dụ đề `:53`: `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}` |
| `cook_started` | thêm `items`: mảng cá thể `{id,kind,fresh}` **sắp theo kind rồi id** | GIẢ ĐỊNH: payload món (`dish` trong `start_cooking` `quan.py:86-88`) thêm `base_price`, lan sang `dish_ready`/`dish_picked`/`served` qua `**dish` |
| `monster_hit.lost`, `faint.lost` | mảng **cá thể** theo thứ tự bỏ LIFO (mới nhất trước) | v1.1 là mảng kind |
| `gather_end.inventory` | `{"items":[…]}` theo id | |
| Snapshot `hold`, `stock` (quán + Shop), `customers[].reserved` | mảng cá thể / mảng id | `fresh` trong JSONL làm tròn 3 chữ số (`jsonl.py:8`); đề cho dung sai ±0.01 |

### 4.3 Số nguyên 240 đơn vị/điểm: vì sao chính xác ở ngưỡng 30

Đã chạy thử (Python 3.13):

| Cách tính | Hàng 100 trong giỏ ươn ở bước | Hàng 100 trong kho quán ươn ở bước |
|---|---|---|
| float: `f -= 0.5/60` | **8400** (f = 29.99999999997329, sai số cộng dồn) | 16801 |
| số nguyên: `u -= 2`, ươn khi `u < 7200` | **8401** (đúng: 24000 − 2·8400 = 7200 vẫn chưa ươn) | 16801 |

- Float ươn **sớm 1 tick** ở giỏ. Tick của event biên phải chính xác (đề `:50`), nên test ẩn bắt được lỗi này.
- Fixture mẫu: `fresh: 30` → 7200 → bước 1: 7198 < 7200 → `spoiled` tick 1. Khớp ví dụ của đề.
- Hàng mới `fresh = 100` lúc nhặt, hao **từ bước sau**: tự đúng nếu hao ở đầu bước (bước 1) còn nhặt ở bước 5–6.
- Đổi khi đọc: `units = round(fresh × 240)`. Giá trị 30, 97.5, 100 cho số nguyên chính xác (97.5 × 240 = 23400.0).
- Đổi khi ghi: `fresh = units / 240`. `json.dump` dùng `repr` ngắn nhất nên đọc lại ra đúng float đó; `round(f × 240)` trả lại đúng `units` (đã thử 23998 → 99.99166666666666 → 23998). **Đừng** ghi file kho qua `jsonl._clean` (làm tròn 3 chữ số): 3 chữ số nhỏ hơn bước 1/240 ≈ 0.00417 nên thường vẫn khôi phục được, nhưng đề đòi "đủ độ chính xác khi đọc lại", nên ghi đầy đủ là an toàn.
- Smoke bàn giao của đề (`:54`): fresh 100 + `interact` frame 0 → hao 1 lần (bước 1) rồi cập bến → file ghi 99.99166666666666 (23998 đơn vị); `quan --ticks 0` phải hiện đúng giá trị đó.
- **Giá**: `base_price = floor(price × trung_bình_fresh / 100)` = `price × Σunits // (n × 24000)`, hoàn toàn số nguyên. Ví dụ: 60 × 23998 // 24000 = **59**; lẩu 120 với [12000, 12000, 12000, 24000] → 120 × 60000 // 96000 = **75**. Boa: `floor(base_price × 0.2)` = `base_price // 5`. Đặt trước: `floor(base_price × 1.5)` = `base_price * 3 // 2`.
- Fixture đề gợi ý "biểu diễn chính xác" → fresh là bội của 1/240. Với fixture lẻ (vd. 33.333) thì `round` lệch < 1/480 điểm, nằm trong dung sai ±0.01.
- Pause dừng hao tươi; món chín không hao; hàng ở Shop hoặc chờ nhập không hao; bàn giao trong `day` không hao thêm ở tick chuyển pha.

---

## 5. Test cũ sẽ vỡ khi bật v1.2

| Test (file:dòng) | Vì sao | Cách sửa |
|---|---|---|
| `tests/test_python_starter_units.py:65` `Session("gather", …, {"hold": ["ca_loc"]})` | hold là chuỗi | `[{"id":"I1","kind":"ca_loc","fresh":100}]` |
| `tests/test_smoke_p1.py:184,197` `test_time_ends_gather_and_keeps_hold` | hold chuỗi; so `{"items":{"ca_loc":1}}` | hold cá thể; so `items == [{"id":"I1","kind":"ca_loc","fresh":≈99.975}]` (3 bước × 2 đơn vị = 23994/240) |
| `tests/test_smoke_p1.py:204,212,215,219` `test_inv_01_gather_writes_inventory_quan_reads_it` | hold chuỗi; file và `stock` dạng đếm | dùng đúng smoke của đề `:54`; so id/kind/fresh từng cá thể |
| `tests/test_smoke_p1.py:85` hold vượt sức chứa | vẫn mã 2 nhưng vì sai schema chứ không vì vượt sức chứa (test đúng nhờ may) | 13 cá thể hợp lệ |
| `tests/test_smoke_p1.py:232-235` `test_inv_bad_schema_exit_2` | vẫn mã 2 nhưng vì "kho đếm" | thêm ca v1.2: kind lạ, `fresh: -1`, `100.5`, id trùng, id rỗng; giữ 1 ca kho đếm → mã 2 |
| `tests/test_smoke_p1.py:239-241` xung đột kho + `quan.stock` | `{"items":{}}` là kho đếm nên mã 2 vì lý do khác | `{"items":[]}` + `stock: []` |
| `tests/test_smoke_p1.py:246-249` cờ kho sai mode | vẫn mã 2 vì kiểm cờ trước | nên đổi sang `{"items":[]}` cho đúng nghĩa |
| `tests/test_smoke_p1.py:93` `{"quan":{"stock":{}}}` chạy gather | vẫn mã 2 (sai khối) | giữ, có thể đổi `stock: []` |

Không vỡ: con_01, con_02, con_03 (inputs/mode), `test_gather_snapshot_has_gather_fields` (không đọc `hold`), Movement, `test_inv_01_not_written_when_tick_limit_first`, `test_live`, `test_team_check`.

Lưu ý: nhiều test "vẫn xanh vì may" ở trên sẽ **che lỗi** adapter. Nên sửa chúng cùng commit bật `"1.2"`, ghi lý do trong commit và `CHANGELOG.md`.

---

## 6. Rủi ro
1. **Nền chưa có**: contract v1.0, lõi P1 quán chưa nối, P2 chưa làm. v1.2 bị chặn bởi v1.1 (6 loại nguyên liệu, `day`). Ưu tiên: P1 → v1.1 → adapter.
2. **Float ở ngưỡng**: phải lưu `units` nguyên trong sim; chỉ đổi ra float khi xuất.
3. **Hai phiên bản trong lúc chuyển**: `read_inventory` phải chọn theo version, không đoán theo dạng file (đề `:13`).
4. **Id duy nhất toàn cục**: một `IdAllocator` cho cả giỏ, kho, mua Chợ và mẫu Ngày sau; `reserve()` mọi id từ scenario/file trước khi `new("I")`.
5. **`customers` lộ dict thô** (`quan.py:68`): `reserved` sẽ ra JSONL nguyên dạng. Phải là mảng id, sắp cố định.
6. `jsonl._clean` làm tròn 3 chữ số: snapshot 29.9996 hiện là `30.0` dù đã ươn. Test nhánh phải dựa vào event/trạng thái (đề `:50`).

## 7. Câu hỏi mở
- Q1: `freshness` đặt ở `tuning.freshness` hay gốc manifest? (GIẢ ĐỊNH `tuning`.)
- Q2: `cook_started` có kèm `base_price` không, hay chỉ payload món giữ `base_price`? (đề `:44` "Payload món giữ cấu trúc, base_price là giá đã chốt".)
- Q3: Trong bước đầu gather, `node_regrown` hay `spoiled` phát trước khi cùng tick?
- Q4: Snapshot cá thể: có thêm trường `spoiled: true` không, hay HUD tự so `fresh < 30`? (đề chỉ yêu cầu HUD nhận ra được.)
- Q5: Với v1.0/v1.1 vẫn chạy được (test regression P1–P2 dùng kho đếm) hay contract trong repo chỉ còn v1.2? Đề `:123` nói "khi chạy v1.2, file kho đếm trả mã 2" → regression P1–P2 phải chuyển fixture sang cá thể.
