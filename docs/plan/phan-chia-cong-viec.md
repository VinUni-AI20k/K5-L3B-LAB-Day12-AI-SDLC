# Phân chia công việc theo phase — NhomF7 (7 người)

> Tổng hợp từ PRD-0 (Phase 1), TICKET-02 (Phase 2), TICKET-03 (Phase 3), TICKET-04 (Phase 4). Chi tiết mốc giờ, AC và chia việc từng phase ở [phase-1.md](phase-1.md), [phase-2.md](phase-2.md), [phase-3.md](phase-3.md), [phase-4.md](phase-4.md).

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

## Phase 1 — PRD-0 (0:00–1:00, Contract v1.0, tag `phase-1`) — ✅ đã có tag `phase-1`

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

**Mục tiêu**: kho đếm → **kho cá thể** `{id,kind,fresh}`, hao tươi, ươn (< 30), giữ chỗ theo id, giá theo độ tươi, HUD độ tươi. Breaking change ở gather, quán, `day` và file kho. **Chi tiết: [phase-3.md](phase-3.md).**

| Người | Việc chính |
|---|---|
| invzble-z | `Item` + adapter 2 schema trong `inventory.py`, khối `freshness` + khóa v1.1 còn thiếu, bàn giao trong `day`, lật v1.2, tag |
| NguyenQuangDunghe161764 | Giỏ cá thể: cấp id, hao 0.5/s, `spoiled` ở `hold`, `--inventory-out` schema mới |
| comtrang378-ship-it | `lost` mảng cá thể LIFO trong `faint`/`monster_hit` |
| Quoosc | Kho quán cá thể, hao 0.25/s, giữ theo id tươi nhất, nhả + giữ lại 1 lần |
| ttkien0710 | Nấu tiêu id, `base_price` theo tươi, `cook_started.items`, `burn` với kho cá thể |
| WorkOfMinh | `scenario.py` mảng cá thể, smoke bàn giao, regression, `docs/verification/phase-3.md` |
| nganhduong123 | HUD độ tươi, ADR 0002, CHANGELOG nháp, clarify, nhật ký AI, retro |

---

## Phase 4 — TICKET-04 "Phát hành v1.0.0" (2:30–3:00, Contract v1.3, tag `phase-4` + Release v1.0.0)

**Mục tiêu**: `bench_cmd` có render, `soak_cmd` 10 Ngày, 3 cảnh báo + tương phản cao, clone sạch ≤ 3 lệnh, Release có zip, retro và phản tư đủ 7 người. **Chi tiết: [phase-4.md](phase-4.md).**

| Người | Vai | Việc chính |
|---|---|---|
| invzble-z | Release / Integrator | Contract v1.3, CHANGELOG, release notes, tag + Release |
| Quoosc | Soak | `chonoi/soak.py` (pair với invzble-z), mở rộng `leaderboard` nếu dư giờ |
| ttkien0710 | Bench (Python) | `chonoi/bench.py`, công thức 5 trường |
| nganhduong123 | Bench (client) + HUD + retro | `?bench=1`, 3 cảnh báo, tương phản cao, điều phối retro |
| comtrang378-ship-it | Chơi thử | Kiểm 3 cảnh báo ở chế độ tương phản cao, hoàn thiện `monsters.py` |
| NguyenQuangDunghe161764 | Đóng gói | Clone sạch, README, zip, CREDITS/LICENSE |
| WorkOfMinh | Bench / QA | Chạy bench + soak, regression P1–P3, `docs/verification/phase-4.md`, checklist demo |
| Cả 7 người | — | `docs/members/<handle>.md` (≤ 200 từ) |
