# Phase 1 — Chia việc 4 người (theo PRD-0)

> **Đọc trước:** [PRD-0](../prd/PRD-0.md) (mục F là luật từng bước) và [hợp đồng](../contracts/README.md) (tên sự kiện + `data`).
> Mỗi người **≥ 3 commit có nội dung**. Hạn tag `phase-1`: **1:00**.

| Người | Lát PRD (6.2) | File chính | Vai | Dự phòng cho |
|---|---|---|---|---|
| **A** | Lát 1 + 2: bơi, oxy, giỏ, hái, bắt cá, cập bến | `chonoi/sim/gather.py` | PO | B |
| **B** | Lát 3 + 4: khách, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, tiền | `chonoi/sim/quan.py` | Scrum | A |
| **C** | Hợp đồng, kiểm scenario, HUD, README | `chonoi/scenario.py`, `chonoi/web/index.html`, `README.md` | Integrator | D |
| **D** | Test, ma trận truy vết, bằng chứng, skill | `tests/test_*_rules.py`, `docs/verification/`, `docs/proof/`, `.agents/skills/` | QA lead | C |

Khung đã có sẵn: bơi + ramp + chặn mép, cập bến → `docked`, hết giờ, ghi file kho, JSONL, sắp/cấp id, RNG. **Không sửa** `runner.py`, `headless.py`, `inputs.py`, `inventory.py`.

---

## A — `gather.py` + PO

Sửa trong `GatherSim.step()` theo đúng thứ tự PRD F/Gather. Số liệu chỉ đọc từ `self.t[...]`.

### Bước 2: bơi → dive/surface → oxy → ngạt (ngay sau `self._move(inp)`)
- [ ] `was_surface = self._at_surface()` **trước** `_move`. Sau khi bơi, nếu đổi phía thì phát `dive` hoặc `surface` với `{"pos": self.pos}`.
- [ ] Oxy theo `d` **cuối bước**:
  - Mặt nước (`d ≤ 0.5`): `oxygen += 6`, kẹp tối đa, **`zero_oxy_ticks = 0`**.
  - Dưới nước: `oxygen -= 1`, kẹp 0. Nếu từ dương về 0 thì phát `oxygen_empty` với `{"oxygen_ticks": 0}`.
- [ ] Dưới nước **và** oxy = 0 (kể cả bước vừa chạm 0) → `zero_oxy_ticks += 1`. Đủ 60 → đặt về 0, `hp -= 1`, phát `choke` với `{"hp": hp}`.
  - Kiểm: chạm 0 ở tick t thì ngạt lần đầu ở **t+59**. Nổi lên đúng bước đáng lẽ ngạt → không ngạt.
- [ ] `hp == 0` → `lost = list(reversed(self.hold))`, `self.hold = []`, phát `faint` với `{"cause":"choke","lost":lost,"hp":0}`, `self._finish("fainted", events)`, `return events`.

### Bước 3: interact (bến đã có, thêm hái)
- [ ] Ngoài bến và `_at_surface()`: chọn nút `regrow_ticks == 0` gần nhất trong `interact_radius` (tính cả đúng mép), hòa thì id nhỏ hơn (`sort_by_id`).
- [ ] `free = hold_capacity - len(hold)`:
  - `free ≥ node_yield`: thêm kind vào giỏ, `regrow_ticks = regrow_s*60`, phát `gather` với `{"node_id","kind","amount":1}`.
  - Thiếu chỗ: phát `hold_full` với `{"action":"gather","node_id","required":1,"free":free}`, nút giữ nguyên.

### Bước 4: catch
- [ ] Chỉ khi `catch_cd_ticks == 0` **và** dưới nước. Chọn đàn gần nhất trong `catch_radius`, hòa thì id nhỏ hơn. Không có đàn → **không sự kiện, không hồi chiêu**.
- [ ] `y = fish_yield[kind]`:
  - Đủ chỗ: thêm `y` con, xóa đàn, phát `fish_caught` với `{"fish_id","kind","yield":y}`, `catch_cd_ticks = round(catch_cooldown_s*60)`.
  - Thiếu chỗ: phát `hold_full` với `{"action":"catch","fish_id","required":y,"free":free}`, **giữ đàn, không đặt hồi chiêu**, không thử đàn khác.

### Bước 5: hết giờ (đã có). Kiểm lại: hái/bắt hợp lệ ở bước cuối vẫn vào kho.

### PO
- [ ] Hỏi Anh Năm 3 điểm mơ hồ trong [hợp đồng mục 5](../contracts/README.md), ghi [docs/clarify.md](../clarify.md).
- [ ] Phút 25: chạy thử xuất file kho thật (`--inventory-out`) để B dùng.

**Commit:** `gather: dive/surface + oxy` · `gather: ngạt/choke/faint` · `gather: hái + hold_full` · `gather: bắt cá + cooldown`

---

## B — `quan.py` + Scrum

Thêm bộ đếm `self.phase_tick` (tăng 1 mỗi bước). Hằng số tick: `patience_full = patience_s*60`, `eat_full = eat_s*60`, `interval = customer_interval_s*60`.

### Mô hình dữ liệu (theo PRD D)
- Khách: `{id, table_id, dish_id, order_tick, state: waiting|eating, patience_ticks_left, eat_ticks_left, order_status: reserved|assigned|unfulfillable|served, reserved: {kind: n}, base_price, tip}`. `order_id` = id khách. Cấp id: `self.ids.new("C")`.
- Món (trên bếp/tay): `{order_id, dish_id, base_price}`.
- `stock` = tồn **vật lý** (gồm phần giữ). Kho khả dụng = `stock − tổng reserved`.

### Thứ tự một bước (PRD F/Quán)
1. [ ] `phase_tick += 1`, giảm `time_left`, `cook_ticks_left`, `eat_ticks_left` (khách eating), `patience_ticks_left` (khách waiting), đều kẹp 0. `ready_ticks += 1` chỉ cho bếp **đã ready từ đầu bước**.
2. [ ] Bếp theo id: `cooking` và `cook_ticks_left == 0` → `ready`, `ready_ticks = 0`, phát `dish_ready` với `{stove_id, order_id, dish_id}`.
3. [ ] `_move`, rồi **tối đa 1** `interact`: lấy đối tượng trong `interact_radius` có khóa nhỏ nhất `(khoảng cách, 0 nếu là bếp / 1 nếu là bàn, id)`. Đối tượng đó không tương tác được → bỏ lượt (không thử cái khác).
   - **Bếp idle:** lấy đơn `reserved` cũ nhất theo `(order_tick, id bàn)`. Trừ `reserved` khỏi `stock`, `reserved = {}`, `order_status = assigned`, `base_price = menu price`. Bếp chuyển `cooking`, `cook_ticks_left = cook_s*60`. Phát `cook_started` với `{stove_id, order_id, dish_id, items (mảng kind sắp theo kind), base_price}`.
   - **Bếp ready + tay trống:** `hand = dish`, bếp về `idle`, phát `dish_picked`.
   - **Bàn có khách mà `order_id == hand.order_id`:** `tip = floor(base_price * tip_rate)` nếu `patience_ticks_left / patience_full ≥ tip_min_patience_ratio`, ngược lại 0. Khách chuyển `eating`, `eat_ticks_left = eat_full`, `order_status = served`. `hand = None`. Phát `served` với `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}`.
4. [ ] Khách theo id bàn:
   - **Eating xong** (`eat_ticks_left == 0`): `amount = base_price + tip`, cộng vào `money`, `earned`, `shift_earned`. `tip > 0` → uy tín `+ tip_reputation` (kẹp). Phát `paid` với `reason: "finished_eating"`. Khách rời bàn.
   - **Còn giờ**, khách waiting có `patience == 0`: uy tín `+ left_reputation_delta` (kẹp), phát `customer_left` với `{order_id, table_id, reason:"patience", reputation}`.
   - **Hết giờ:** khách đang ăn trả tiền ngay (`paid`, `reason:"closing"`). Khách đang chờ rời với `customer_left` `reason:"closing"`, **không trừ uy tín**. Sau đó phát `quan_end` (khung đã có).
   - Khi khách rời: nhả `reserved` (chỉ bỏ giữ, **không** trừ stock), bỏ món của đơn đó trên bếp (về idle) hoặc trên tay (`hand = None`). Nguyên liệu đã nấu không hoàn lại.
5. [ ] **Còn giờ** và `random_customers` bật và `phase_tick == first_customer_tick + n*interval`:
   - Không bàn trống → bỏ lượt (không phát gì).
   - Có bàn trống → lấy bàn id nhỏ nhất. Lọc các món đủ nguyên liệu khả dụng (duyệt id món theo thứ tự chữ). Không món nào → phát `no_dish` với `{}`. Có món → chọn đều bằng `self.rng.get("customers").choice(list)`.
   - Khách mới: `order_tick = phase_tick`, kiên nhẫn đầy, `reserved` = công thức, `state = waiting`, `order_status = reserved`. Phát `customer_arrived` với `{order_id, table_id, dish_id}`.
- [ ] `__init__`: khách từ scenario thiếu `reserved` ở đơn reserved → cấp theo công thức (theo `order_tick` rồi id bàn). Đọc `random_customers`.
- [ ] `snapshot()`: đủ trường như [hợp đồng mục 3](../contracts/README.md), `player` có `vel`.

### Scrum
- [ ] [docs/standup.md](../standup.md) ở phút 20 và 35 (đã xong / sắp làm / vướng). Phút 20 rà lát chậm, điều người rảnh sang giúp.

**Commit:** `quan: lịch khách + chọn món + giữ chỗ` · `quan: kiên nhẫn + customer_left + đóng ca` · `quan: bếp nấu/chín/bưng` · `quan: phục vụ, boa, trả tiền, uy tín`

---

## C — Hợp đồng + scenario + HUD + README + Integrator

### Ngay (đã có bản nháp — rà lại rồi commit)
- [ ] [docs/contracts/README.md](../contracts/README.md), [TEAM.md](../../TEAM.md) (4 người + thỏa thuận), `game.contract.json` (`team`).
- [ ] Commit khởi động, push, báo cả nhóm `git pull`.

### Kiểm scenario quán → mã 2 (`chonoi/scenario.py`, `_validate_quan`; PRD D)
- [ ] Trường khách lạ ngoài danh sách D; `dish_id` không có trong menu; `state` / `order_status` ngoài miền; bộ đếm âm.
- [ ] `reserved` khác công thức món; tổng `reserved` vượt `stock`.
- [ ] Đơn `assigned` phải có đúng một món ở bếp hoặc tay, và `reserved` rỗng.
- [ ] Bếp `cooking` phải có `cook_ticks_left > 0` và món khớp một đơn. Bếp và tay không được giữ cùng một đơn.
- [ ] Khách `eating` phải là `served`, có `eat_ticks_left > 0` và có `base_price`, `tip`.
- [ ] `unfulfillable`: `reserved` rỗng, không có món.
- [ ] `hand` phải là payload hợp lệ của một đơn có thật.
- [ ] Cho phép thêm trường bếp `state, dish, cook_ticks_left, ready_ticks`.

### HUD (`chonoi/web/index.html`, chỉ đọc snapshot; PRD mục 2)
- [ ] Gather: thời gian, oxy, Máu, giỏ (starter đã có). Thêm chữ báo khi có `choke`, `faint`, `hold_full`.
- [ ] Quán: kho **khả dụng** (`stock − reserved`), món khách gọi, thanh kiên nhẫn, trạng thái bếp, món trên tay (`hand.dish_id`), tiền, uy tín.

### README (DoD)
- [ ] Cách chạy từ clone sạch (≤ 3 lệnh trên macOS/Linux), điều khiển, cách tính điểm, lệnh test 1 dòng, mục "Sáng tạo của nhóm" (nếu có).

### Integrator
- [ ] Merge mỗi 15–20 phút. Phút 45: smoke hai tiến trình trên `main` (lệnh ở PRD G). Trước 1:00: `git tag phase-1 && git push origin phase-1`.

**Commit:** `contracts + TEAM` · `scenario: kiểm mâu thuẫn quán` · `ui: HUD quán` · `README: chạy, điều khiển, điểm`

---

## D — Test + bằng chứng + harness

Viết test hộp đen bằng `run_headless` + scenario/inputs (mẫu: `tests/test_smoke_p1.py`). Viết **ngay**, không chờ A/B. Đỏ trước, xanh sau.

### AC Phase 1 (dùng làm ID trong ma trận truy vết)
| AC | Nội dung kiểm |
|---|---|
| AC-P1-01 | Lặn: oxy −1/tick. Mặt nước: +6/tick, kẹp max |
| AC-P1-02 | `dive` / `surface` chỉ khi đổi phía, `data.pos` |
| AC-P1-03 | Oxy chạm 0 ở t → `oxygen_empty`; `choke` lần đầu ở t+59, `hp` giảm 1 |
| AC-P1-04 | Nổi lên đúng bước đáng lẽ ngạt → không `choke` |
| AC-P1-05 | `hp: 1` ngạt → `faint` (`lost` theo LIFO) → `gather_end fainted`, file kho `{"items":{}}` |
| AC-P1-06 | Hái đúng mép bán kính (scenario PRD D: player `[20,0]`, nút `[22,0]`) → `gather amount 1`, `regrow_ticks = 1200` |
| AC-P1-07 | Hái khi giỏ đầy → `hold_full action gather`, nút giữ nguyên |
| AC-P1-08 | Nút mọc lại sau 1200 tick → `node_regrown` |
| AC-P1-09 | Bắt cá linh → `fish_caught yield 3`, giỏ +3, hồi 30 tick |
| AC-P1-10 | Bắt khi thiếu chỗ → `hold_full action catch`, đàn còn, không hồi chiêu |
| AC-P1-11 | Bắt ở mặt nước / không có đàn trong tầm → không sự kiện |
| AC-P1-12 | Smoke 2 tiến trình (`dock.json` ở PRD G) → quán tick 0 `stock {"bong_sung":2,"ca_loc":1}` |
| AC-P1-13 | Khách đầu tiên ở `phase_tick` 120, tiếp theo mỗi 900 tick, giữ chỗ đúng công thức |
| AC-P1-14 | Kho rỗng + bàn trống → `no_dish {}` |
| AC-P1-15 | Hết kiên nhẫn → `customer_left patience`, uy tín 3.0 → 2.5 |
| AC-P1-16 | Chuỗi `cook_started → dish_ready → dish_picked → served → paid`, `amount = base_price + tip` |
| AC-P1-17 | Boa: phục vụ khi kiên nhẫn ≥ 50% → `tip = floor(price*0.2)`, uy tín +0.2; < 50% → tip 0 |
| AC-P1-18 | Hết ca: khách đang ăn `paid closing`, khách chờ `customer_left closing` không trừ uy tín, rồi `quan_end` |
| AC-P1-19 | Cùng seed + inputs → JSONL và file kho giống từng byte |
| AC-P1-20 | Scenario quán mâu thuẫn (giữ quá tồn, eating thiếu giá…) → mã 2 |

- [ ] `tests/test_gather_rules.py` (AC 01–12), `tests/test_quan_rules.py` (AC 13–20).
- [ ] [docs/verification/phase-1.md](../verification/phase-1.md): AC → cách kiểm → link `docs/proof/phase-1/...` → đạt/chưa đạt (trung thực).
- [ ] `docs/proof/phase-1/`: log test chạy ở commit sắp tag + `gather.jsonl`, `catch.json`, `quan.jsonl` của smoke.
- [ ] `.agents/skills/run-tests-proof/SKILL.md` và `.agents/skills/check-determinism/SKILL.md`; ghi tên vào mục "Skills / hooks" của [AGENTS.md](../../AGENTS.md).

**Commit:** `test: luật gather` · `test: luật quán` · `skills: run-tests-proof + check-determinism` · `verification + proof phase-1`

---

## Lịch (PRD 6.4)

| Phút | A | B | C | D |
|---|---|---|---|---|
| 0–15 | Đọc PRD F/Gather, hỏi Anh Năm | Đọc PRD F/Quán | Commit khởi động (TEAM, hợp đồng) | Đọc PRD, lên khung test |
| 15–25 | Oxy, ngạt, faint | Khách + giữ chỗ | Kiểm scenario | Test gather |
| 25–45 | Hái, bắt cá | Bếp, phục vụ, tiền, đóng ca | HUD, README, merge | Test quán, skill |
| 45–55 | Sửa lỗi theo test | Sửa lỗi theo test | Smoke 2 tiến trình, merge cuối | Verification + proof |
| 55–60 | — | — | **Tag `phase-1`** | Kiểm tag chạy được |

## Tránh conflict
- **Mỗi file một chủ** (bảng đầu trang). Cần sửa file của người khác thì nhắn chủ file.
- Nhánh ngắn (`a/...`, `b/...`, `c/...`, `d/...`). Trước push: `git pull --rebase origin main` + chạy test. **Chỉ C merge vào `main` và gắn tag.**
- `docs/ai-usage-log.md`: mỗi người ghi vào mục của mình. `docs/members/<handle>.md`: mỗi người một file.
- Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows: copy `python.exe` thành `python3.exe` trong thư mục Python).
