# Phân chia công việc theo phase — NhomF7 (7 người)

> Tổng hợp từ PRD-0 (Phase 1), TICKET-02 (Phase 2), TICKET-03 (Phase 3). Chi tiết mốc giờ từng phase ở `docs/plan/phase-<n>.md`. Phase 4 chưa phát hành, sẽ bổ sung khi có ticket.

## 0. Nguyên tắc chung (giữ suốt 4 phase)

| Người | Handle | Vai cố định | "Nhà" trong code | Dự phòng cho |
|---|---|---|---|---|
| Nguyễn Khắc Bào | invzble-z | Integrator + Release | `game.contract.json`, `docs/contracts/`, `runner.py`, `headless.py`, `inventory.py`, `sim/day.py` | WorkOfMinh |
| Nguyễn Ánh Dương | nganhduong123 | PO | `chonoi/web/`, `chonoi/live.py`, `docs/` (clarify, plan, standup, ai-usage-log, retro), `AGENTS.md` | invzble-z |
| Nguyễn Anh Tú | comtrang378-ship-it | Dev gather | `sim/gather.py` phần oxy/Máu/ngất, `sim/monsters.py` | NguyenQuangDunghe161764 |
| Nguyễn Quang Dũng | NguyenQuangDunghe161764 | Dev gather | `sim/gather.py` phần hái/bắt cá/giỏ/cá bơi | comtrang378-ship-it |
| Phạm Trấn Quốc | Quoosc | Dev quán | `sim/quan.py` phần khách/giữ chỗ/kiên nhẫn | ttkien0710 |
| Trần Trung Kiên | ttkien0710 | Dev quán | `sim/quan.py` phần bếp/bưng/phục vụ/tiền | Quoosc |
| Hoàng Minh | WorkOfMinh | QA lead + Scrum | `tests/`, `chonoi/scenario.py`, `docs/proof/`, `docs/verification/` | nganhduong123 |

- **Giữ "nhà" qua các phase**: mỗi người tiếp tục module mình đã viết, nên đổi luật ở phase sau không phải đọc lại code người khác.
- **Một hàm, một chủ.** Sửa vùng của người khác thì báo chủ trước. Đổi schema/contract phải qua Integrator.
- **Không chờ nhau**: mỗi lát test bằng scenario/fixture riêng, file test riêng `tests/test_p<n>_<lát>.py`.
- **Git**: nhánh ngắn `p<n>/<lát>`, PR nhỏ, người dự phòng review, chạy test trước khi mở PR. Chỉ Integrator gộp vào `main` và gắn tag.
- **Mỗi người ≥ 3 commit có nội dung cả buổi** (gợi ý ≥ 1 commit/phase). Làm chung thì ghi `Co-authored-by:`.
- **Nhịp mỗi phase**: lên kế hoạch → làm song song → smoke tích hợp ở phút 20 + standup → regression + verification → tag → retro.
- **Mở rộng**: nhóm 7 người giả định cần ≥ 2 mục cho cả buổi lab (`docs/clarify.md` #2). Chỉ làm khi lõi đã xanh.

---

## Phase 1 — PRD-0 (0:00–1:00, Contract v1.0, tag `phase-1`) — ⚠️ chưa thấy tag `phase-1` trên repo, Integrator cần gắn

**Mục tiêu**: chơi được `gather` và `quan` riêng, nối qua file kho.

| Lát | Người | Việc | Phụ thuộc |
|---|---|---|---|
| Khung + hợp đồng | invzble-z | Chốt `docs/contracts/` (schema kho, event, trường khách/bếp), commit khung `step()` chia hàm rỗng, `game.contract.json` v1.0, `team_size: 7` | Làm đầu tiên (0:00–0:15) |
| G1 Bơi, oxy, chặn biên | comtrang378-ship-it | Oxy, ngạt, Máu, ngất, dive/surface/choke/faint | Commit khung |
| G2 Hái, bắt cá, giỏ, ghi kho | NguyenQuangDunghe161764 | Hái ở mặt nước, bắt cá, giỏ 12 ô, cập bến, `--inventory-out` ghi nguyên tử | Commit khung |
| Q3 Khách, giữ chỗ, kiên nhẫn | Quoosc | Lịch khách, chọn món theo seed, giữ nguyên liệu, `no_dish`, rời bàn trừ uy tín | Hợp đồng khách |
| Q4 Bếp, bưng, phục vụ, tiền | ttkien0710 | Nấu → ready → bưng → giao, boa, paid, uy tín | Hợp đồng khách (dựng khách bằng scenario) |
| QA | WorkOfMinh | Test hộp đen theo AC-P1, scenario mâu thuẫn → mã 2, smoke 2 tiến trình, `docs/verification/phase-1.md`, `docs/proof/phase-1/` | AC từ PRD-0 |
| PO + harness | nganhduong123 | TEAM.md, thỏa thuận nhóm, `docs/clarify.md`, `AGENTS.md`, skill `.agents/skills/`, HUD tối thiểu (UI web) | Không |

---

## Phase 2 — TICKET-02 "Một ngày ở chợ nổi" (1:00–1:55, Contract v1.1, tag `phase-2`)

**Mục tiêu**: số chuẩn, 6 nguyên liệu/6 món, cá bơi/sinh, Cá Sấu + Máu/ngất, 2 bếp/4 bàn, `--mode day` D1–D5 + Shop + nâng cấp, menu/pause/HUD.

### Chia việc
| Lát | Người | Việc cụ thể (theo ticket) | Đầu vào cần có | Bàn giao |
|---|---|---|---|---|
| 1a. Số chuẩn + contract v1.1 | invzble-z | `contract_version:"1.1"`, toàn bộ khóa §4.1: tuning gather mới, `gather.monsters`, `quan` (B2, T2–T4), 6 món, `day_plan` D1–D5, `shop.upgrades` | Ticket §1–2 | `game.contract.json` lúc phút 5–10 (mọi lát đọc số từ đây) |
| 1b. Cá bơi + sinh | NguyenQuangDunghe161764 | 8 đàn đầu ca, bơi 1.5 m/s, đổi hướng mỗi 120 bước, phản xạ mép, sinh theo lịch 360·k (trần 12, cách > 1 m, trọng số 40/30/30), `fish_spawned`, N5/N6, `ca_keo`/`keo_neo`, `age_ticks`, `random_fish` | Khóa cá ở 1a | `fish[]` trong snapshot đúng thứ tự xử lý |
| 2. Cá Sấu, Máu, ngất | comtrang378-ship-it | `sim/monsters.py`: patrol/chase/recoil, M1 (M2 từ Ngày 3), hit ≤ 1.5 m, bỏ floor(n/2) LIFO, bất tử 90 tick, `monster_hit`, `faint.cause:"monster"`, scenario `gather.monsters[]`, snapshot `monsters[]`, `invuln_ticks` | Khóa `gather.monsters` | Thứ tự trong tick: bơi/oxy → quái/hit → tương tác → bắt cá → hết giờ |
| 3a. Khách 4 bàn + kế hoạch | Quoosc | Lịch 120 + 900·k, bàn trống id nhỏ nhất, lọc menu theo kế hoạch trước khi lọc nguyên liệu (trong `day`), quán riêng dùng 6 món, `no_dish` | Khóa `quan`, `day_plan` | Hàm `QuanSim` nhận `menu_filter` từ day |
| 3b. 2 bếp + 6 món | ttkien0710 | B1/B2 lấy đơn reserved cũ nhất (order_tick → id bàn), chọn đối tượng gần nhất (bếp trước bàn → id), 6 món đọc từ dữ liệu, đóng ca dọn món | Khóa `menu` | — |
| 4a. Vòng ngày + Shop (sim) | invzble-z (sau 1a) | `sim/day.py`, `--mode day --days N`, đổi pha day_start → day_plan → phase_start, bàn giao kho trong bộ nhớ, Shop (`buy`, `shop_done`, 600 tick, `bought`/`buy_failed`/`shop_end`), `pause`/`resumed`, `upgrades` vs `active_upgrades`, `days_completed`, scenario khối `day` | 1a + `GatherSim`/`QuanSim` hiện có | Snapshot day có `day`, `day_plan`, `upgrades`, `active_upgrades` |
| 4b. Menu, intro, pause, HUD, Shop UI | nganhduong123 | Menu Chơi/Thoát, DayIntro (4 s), EveningIntro, DayResult, Summary, pause làm mờ nền, HUD sáng (Máu, oxy < 25% nhấp nháy, giờ ≤ 30 s, cần/đã lấy, "Thủy quái!", "Hết hơi!"), HUD quán (kiên nhẫn từng bàn, tiến độ 2 bếp), chữ ≥ 18 px, ≥ 30 FPS | Trường snapshot đã chốt (dùng mock khi 4a chưa xong) | `chonoi/web/` |
| QA | WorkOfMinh | Phút 20: smoke `gather --inventory-out` → `quan --inventory` lưu `docs/proof/phase-2/integration.*`. Phút 35: smoke `day --days 1`, `day --days 3` (kiểm M2 + nâng cấp từ Ngày kế), regression P1 với số chuẩn (ghi lý do test đổi), test headless 1 Ngày ≤ 20 s, `docs/verification/phase-2.md` | Từng lát gộp vào main | Ma trận AC → bằng chứng |
| PO | nganhduong123 | Chốt giao diện chuyển pha ở phút 0–5 vào `docs/contracts/`, cập nhật `docs/clarify.md` (#2–#4), `docs/ai-usage-log.md`, điều phối retro `docs/retro.md` | — | — |

### Mở rộng Phase 2 (sau khi lõi xanh, chọn 2 mục rẻ nhất, tận dụng code sẵn có)
| Mục | Người | Lý do chọn |
|---|---|---|
| `burn` (Cháy món) | ttkien0710 | Chỉ thêm `burn_s: 20` và nhánh `ready_ticks > 1200` trong bếp của chính Kiên |
| `snake` (Rắn Hổ Mây) | comtrang378-ship-it | Dùng lại luật chạm/recoil của Cá Sấu, chỉ thêm loài `ran` + spawn M3 |
Khai `extensions` ở gốc manifest, ghi README + test. Nếu hết giờ, bỏ mở rộng, không để lõi đỏ.

### Đường găng và cách gỡ
- **4a (day) là đường găng**: invzble-z làm 1a thật nhanh (≤ phút 10) rồi chuyển sang 4a. WorkOfMinh viết fixture `day` sớm để 4a test ngay.
- 4b không chờ 4a: dùng mock (`/?mock=day-shop`) theo trường snapshot đã chốt.
- Người xong sớm (thường 3b, 1b) chuyển sang hỗ trợ 4a hoặc làm mở rộng.

---

## Phase 3 — TICKET-03 "Mùa Nước Nổi" (1:55–2:30, Contract v1.2, tag `phase-3`)

**Mục tiêu**: kho đếm → **kho cá thể** `{id,kind,fresh}`, hao tươi, ươn (< 30), giữ chỗ theo id, giá theo độ tươi, HUD độ tươi. Đây là **breaking change** ở cả gather, quán, day và file kho.

### Phút 0–7: phân tích tác động (PO ghi, Integrator chốt)
| Module | File cần đổi | Test bị ảnh hưởng | Người |
|---|---|---|---|
| Adapter / schema kho | `chonoi/inventory.py`, `chonoi/scenario.py` (hold/stock/reserved thành mảng), `game.contract.json` (khối `freshness`), `docs/contracts/` | Test đọc/ghi kho v1.0 → đổi sang v1.2, thêm test kho đếm → mã 2 | invzble-z |
| Lặn | `sim/gather.py` (cấp id khi vào giỏ, hao 0.5/s, `spoiled` location hold), `sim/monsters.py` (`lost` thành mảng cá thể LIFO) | Test hái/bắt/ngất/monster_hit đổi format `hold`, `lost` | NguyenQuangDunghe161764 (giỏ, id, hao, spoiled) + comtrang378-ship-it (lost trong monster_hit/faint) |
| Quán | `sim/quan.py` (hao 0.25/s, spoiled location stock, giữ theo id, nhả + giữ lại 1 lần, giá theo fresh) | Test giữ chỗ, nấu, giá đổi | Quoosc (giữ chỗ theo id, xử lý ươn) + ttkien0710 (tiêu id khi nấu, `base_price`, `cook_started.items`) |
| day | `sim/day.py` (bàn giao cùng tick không hao thêm, id I1.. tăng xuyên Ngày, `gather.hold` Ngày kế cấp id mới) | Test day bàn giao | invzble-z |
| HUD | `chonoi/web/` (thanh/số độ tươi, nhãn "ươn") | Test live static | nganhduong123 |
| QA | `tests/test_p3_*.py`, `docs/proof/phase-3/`, `docs/verification/phase-3.md` | Regression P1–P2 còn hiệu lực, ghi lý do test bị thay | WorkOfMinh |

### Quyết định kỹ thuật chốt sớm (ghi `docs/adr/0002-kho-ca-the.md`)
- **Biểu diễn độ tươi bằng số nguyên**: 240 đơn vị = 1 điểm tươi (100 điểm = 24 000). Gather trừ 2 đơn vị/tick, quán trừ 1 đơn vị/tick. So ngưỡng 30 (= 7 200) trên số nguyên trước khi làm tròn → không lệch dấu phẩy động.
- **Một kiểu `Item(id, kind, fresh_units)` dùng chung** đặt trong `chonoi/inventory.py`; gather/quán/day chỉ dùng kiểu này.
- **`IdAllocator` cho `I<n>` là một bộ đếm duy nhất** giữ trong DaySim, truyền xuyên pha và Ngày.
- **Chuyển đổi an toàn**: adapter đọc theo `contract_version` (1.1 → kho đếm, 1.2 → kho cá thể). Chỉ lật `contract_version:"1.2"` khi cả gather và quán đã xong, để `main` luôn chạy.

### Thứ tự tích hợp (giữ main xanh)
1. **Phút 7–12** — invzble-z: `Item`, adapter đọc/ghi 2 schema, scenario mảng cá thể, khối `freshness`. Gộp trước, các lát khác rebase.
2. **Phút 12–25** — song song: Lặn (Dũng + Tú), Quán (Quốc + Kiên), HUD (Dương, dùng mock snapshot có `fresh`), QA viết test ngưỡng/giữ lại/giá trước (test đỏ trước, xanh sau).
3. **Phút 20** — QA chạy smoke bàn giao: gather 1 bước với `fresh:100` + `interact` frame 0 → `quan --inventory --ticks 0`, so chính xác id/kind/fresh. Standup, điều người xong sang lát trễ.
4. **Phút 25** — invzble-z lật v1.2, cập nhật fixture; nối day (bàn giao cùng tick).
5. **Phút 25–32** — QA: smoke file + `day`, regression P1–P2, `docs/verification/phase-3.md`. invzble-z: `CHANGELOG.md` (breaking change, schema mới, cách sửa fixture) và gắn tag. PO: retro về lần đổi kho.
6. **Phút 32–35** — dự phòng, đẩy `phase-3` ≤ 2:30.

### Test bắt buộc (WorkOfMinh giữ, chủ lát viết test của lát mình)
| Test | Người viết |
|---|---|
| Ngưỡng: `fresh:30` trong giỏ → `spoiled` ở tick 1 (scenario mẫu của ticket) | NguyenQuangDunghe161764 |
| `lost` trong `monster_hit`/`faint` là mảng cá thể LIFO | comtrang378-ship-it |
| Hàng giữ chỗ vừa ươn → nhả, giữ lại 1 lần, thiếu → `unfulfillable` | Quoosc |
| `base_price = floor(giá × trung bình fresh / 100)`, boa tính trên giá đã chốt | ttkien0710 |
| Kho đếm khi chạy v1.2 → mã 2; id trùng / fresh ngoài miền → mã 2 | invzble-z |
| Smoke bàn giao file + day, regression P1–P2 | WorkOfMinh |

### Mở rộng Phase 3 (chỉ khi lõi v1.2 xanh trước phút 25)
- `current` (Dòng nước lũ) — NguyenQuangDunghe161764 hoặc comtrang378-ship-it (chỉ cộng lực vào player ở d ≥ 10).
- `reservations` (Khách đặt trước) — Quoosc + ttkien0710, phức tạp hơn, chỉ làm nếu dư nhiều thời gian.
Nếu Phase 2 đã đủ 2 mở rộng, Phase 3 **ưu tiên chất lượng lõi** hơn thêm mục.

---

## Phase 4 — chưa phát hành (2:30–3:00)

Khi ticket ra:
1. PO đọc ticket, gom câu hỏi vào `docs/clarify.md` trong 3 phút đầu.
2. Integrator lập bảng tác động theo mẫu Phase 3, giữ nguyên "nhà" của từng người ở mục 0.
3. QA xác định AC-P4-xx và regression còn hiệu lực.
4. Chừa 5 phút cuối để mỗi người viết phản tư `docs/members/<handle>.md` và hoàn thiện `docs/retro.md`, `docs/ai-usage-log.md`.
