# Kế hoạch Phase 2 — TICKET-02 (hạn tag `phase-2` 1:55)

**Mục tiêu:** contract v1.1 với số chuẩn; cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn, 6 món; `--mode day` chạy trọn vòng D1–D5 với Shop + pause; menu/HUD; regression P1 xanh với số chuẩn. Đề: [`docs/prd/phase-2.md`](../prd/phase-2.md).

## Việc / người / phụ thuộc

| # | Việc | Người | File chính | Phụ thuộc | AC |
|---|---|---|---|---|---|
| 0 | **Khung v1.1 — làm và push TRƯỚC (≤ 10 phút):** `game.contract.json` v1.1 (số chuẩn, N5/N6, 8 cá + khóa cá bơi/sinh, `monsters`, B2 + T2–T4, 6 món, `day_plan`, `shop`); `KINDS` thêm `ca_keo`, `keo_neo`; nút input `pause`, `shop_done`, `buy`; CLI `--mode day`, `--days`; `contract.py` kiểm khóa mới | NgChiVinh | `game.contract.json`, `chonoi/{inventory,inputs,headless,contract,scenario}.py`, `docs/contracts/` | — | AC-P2-01 |
| 1 | Lát 1: số chuẩn gather, cá bơi (1.5 m/s, đổi hướng theo seed mỗi 120 bước, phản xạ mép), sinh cá (8 đầu ca, trần 12, mỗi 360 tick, trọng số loài), `fish_spawned`, `age_ticks`, cá kèo yield 2 | TrungHieuPh | `chonoi/sim/gather.py` (bước "cá bơi, sinh"), `scenario.py` (fish) | 0 | AC-P2-02 |
| 2 | Lát 2: Cá Sấu M1/M2 (patrol/chase/recoil, chặn dải độ sâu), `monster_hit` (−1 Máu, bỏ floor(n/2) LIFO, bất tử 90), `faint` cause `monster`, `monsters[]` trong snapshot/scenario | 22520160 | `chonoi/sim/gather.py` (bước quái), `chonoi/sim/monsters.py` (mới), `scenario.py` (monsters) | 0 | AC-P2-03 |
| 3 | Lát 3: 2 bếp/4 bàn (kiểm lại code đa bếp/bàn), 6 món; **review + thêm test cho `chonoi/sim/shop.py`** và `menu_filter` (NgChiVinh đã viết khi làm #4 để không bị chặn); mở rộng **Cháy món** | HoangQuan23112004 | `chonoi/sim/quan.py`, `chonoi/sim/shop.py` (mới) | 0 | AC-P2-04, AC-P2-05 |
| 4 | Lát 4: **`--mode day`**: chuyển pha `day_start → day_plan → phase_start(gather) → gather_end → phase_start(quan) → quan_end → phase_start(shop) → shop_end`, mang tiền/earned/uy tín/cấp qua Ngày, `active_upgrades` từ Ngày kế (oxy/Máu), `days_completed`, `days_complete`; **pause** (cả 3 mode, `paused`/`resumed`, timer đứng yên) | NgChiVinh | `chonoi/day.py` (mới), `chonoi/runner.py` | 0; dùng fixture cố định để tích hợp sớm với gather/quan/shop | AC-P2-06, AC-P2-07 |
| 5 | UI: menu chính, DayIntro/EveningIntro/DayResult/Shop/Summary, menu pause (Esc/P), HUD sáng v1.1 (độ sâu, đã lấy/cần, hồi bắt, "Thủy quái!", "Hết hơi!"), HUD quán 4 bàn/2 bếp, chữ ≥ 18 px ở 1280×720; `live.py` chạy `--mode day` | truclamld | `chonoi/web/index.html`, `chonoi/live.py` | 0, 4 (đọc snapshot day) | AC-P2-08 |
| 6 | QA: regression P1 với số chuẩn (test cũ đổi phải ghi lý do), smoke tích hợp phút 20 → `docs/proof/phase-2/integration.*`, smoke `day --days 1` và nhiều Ngày, `docs/verification/phase-2.md` | khoa-asta | `tests/`, `docs/proof/phase-2/`, `docs/verification/phase-2.md` | 0 (phút 20), 4 (phút 35) | AC-P2-09 |
| 7 | Clarify với Anh Năm hàng xóm (danh sách mở rộng, chỗ mơ hồ v1.1), retro nhanh `docs/retro.md` | TrungHieuPh (PO), truclamld (Scrum) | `docs/clarify.md`, `docs/retro.md` | — | — |

**AC (rút từ DoD TICKET-02):**
- AC-P2-01: `contract_version` "1.1", tuning chuẩn, 6 nguyên liệu, 6 món, `day_plan`, `shop` theo dữ liệu.
- AC-P2-02: cá bơi/sinh đúng mục 1.1 (tất định theo seed).
- AC-P2-03: Cá Sấu, Máu, ngất đúng mục 1.2.
- AC-P2-04: 2 bếp / 4 bàn / 6 món hoạt động; trong day lọc menu theo kế hoạch.
- AC-P2-05: Shop mua oxygen/hp đúng giá, `buy_failed` khi thiếu tiền / tối đa, đóng bằng `shop_done` hoặc 600 tick.
- AC-P2-06: `--mode day` công bố đúng kế hoạch D1–D5, chốt Ngày khi Shop đóng, cấp có hiệu lực từ Ngày kế; một Ngày ≤ 22.200 tick chạy ≤ 20 s.
- AC-P2-07: pause dừng mọi timer, `paused`/`resumed`.
- AC-P2-08: chơi trọn vòng ngày có menu, pause, HUD theo mục 2.
- AC-P2-09: smoke tích hợp + regression P1 có bằng chứng khớp commit gắn tag.

## Giao diện chuyển pha (chốt ở phút 0–5)
- Mỗi pha là một sim có cùng giao diện: `step(inp) -> events`, `snapshot()`, `done`, `reason`, `mode`/`phase` — như `GatherSim`, `QuanSim` hiện có. `ShopSim(tuning, money, purchased, stock)` theo cùng giao diện.
- `day.py` giữ trạng thái xuyên Ngày (`money`, `earned`, `reputation`, `upgrades`, `active_upgrades`, `days_completed`), dựng sim pha mới từ trạng thái đó, chuyển kho bằng `gather_sim.inventory_items()` (trong bộ nhớ, schema G).
- `GatherSim` nhận `oxygen_max_ticks`/`hp_max` hiệu lực qua tham số (từ `active_upgrades`), không đọc thẳng tuning khi chạy day.
- `QuanSim` nhận `menu_filter` (id món trong kế hoạch Ngày) và tiền/uy tín đầu ca.

## Mở rộng (nhóm 6 người ≥ 2 mục cho cả lab — làm SAU khi lõi xanh)
Đề xuất rẻ nhất trên code hiện có: **Rắn Hổ Mây** (`snake`, dùng lại code Cá Sấu — 22520160) và **Cháy món** (`burn`, vài dòng trong quán — HoangQuan23112004). Khai mã ở `extensions` của manifest + README + test.

## Mốc
- Phút 0–5: đọc đề, chốt kế hoạch + giao diện chuyển pha.
- Phút 10: khung v1.1 trên `main` (#0) — mọi lát rebase lên.
- Phút 20: smoke tích hợp gather → quan với số chuẩn (Khoa), standup, điều người.
- Phút 35: smoke `day --days 1` và nhiều Ngày; regression P1.
- Phút 45: verification + retro; Integrator gắn tag `phase-2`.

## Rủi ro
- Khung v1.1 chặn mọi lát → Vĩnh push trong 10 phút; trong lúc chờ, các lát đọc PRD và viết test hộp đen trước.
- Lát 1 và lát 2 cùng sửa `GatherSim.step` → lát 2 viết quái trong file riêng `monsters.py`, chỉ chèn một lời gọi ở bước "quái"; lát 1 chỉ sửa bước "cá bơi, sinh" cuối `step`.
- Số chuẩn đổi số cá (6 → 8), nút, bàn → nhiều test P1 đổi kỳ vọng: Khoa sửa có ghi lý do, không sửa luật cho xanh.
- `--mode day` là phần lớn nhất và đến cuối mới ghép được → dùng fixture cố định, Shop có giao diện sim giống hai pha kia.
- Bài học P1: sau khi gỡ conflict phải chạy cả bộ test (skill `run-tests`) trước khi push.
