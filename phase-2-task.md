# Bảng công việc Phase 2 (1:00–1:55 · Test Contract v1.1)

> **Lưu ý quan trọng:** Chỉ bắt đầu thực hiện bảng này **sau khi đã gắn tag `phase-1`** (tránh làm hỏng Test Contract v1.0 của Phase 1).

**Quy ước:** đợt 1 làm ngay lúc 1:00, đợt 4 làm cuối. Task nào ghi "Chờ" thì phải đợi task đó xong rồi mới làm. Trong lúc chờ, làm tiếp task khác của mình ở đợt thấp hơn.

**Danh sách thành viên:** Huy (`huyvu-03` — M1) · Quang (`QuangNEU` — M2) · Cao (`ththanh8888` — M3) · Minh (`NhMinh-2610` — M4) · Thanh (`thanhvu101` — M5) · An (`K0heii` — M6, kiêm PO/Integrator).

| Đợt | Mã task | Người | Module | Việc cần làm | Chờ ai / task nào | Ai chờ mình |
|---|---|---|---|---|---|---|
| **1** (1:00–1:05, làm ngay) | M6.1 | An (M6) | M6 | Nâng `game.contract.json` lên `contract_version: "1.1"` (số chuẩn v1.1: 6 nguyên liệu, 6 món, N5/N6, B2, T2–T4, `day_plan` D1–D5, `shop.upgrades`, `monsters`, cá bơi/sinh); cập nhật `docs/contracts/README.md` v1.1 | Tag `phase-1` | **Tất cả** (chặn mọi task .2) |
| 1 | M6.2 | An (M6) | M6 | Cập nhật khung CLI/Input/Kho v1.1: `inventory.py` (thêm `ca_keo`, `keo_neo`), `headless.py` (`--mode day`, `--days 1..5`), `inputs.py` (`pause`, `shop_done`, `buy`), ghi `docs/clarify.md` & `docs/plan/phase-2.md` | M6.1 | **M1.3, M2.3, M3.3, M4.3** |
| 1 | M1.1 | Huy (M1) | M1 | Spec: AC Cá Sấu Năm Chèo (`M1`, `M2` từ Ngày 3), `patrol`/`chase`/`recoil`, `monster_hit`, rơi `floor(hold/2)` LIFO, `invuln_ticks: 90`, `faint cause:"monster"` | Không | M1.2 |
| 1 | M2.1 | Quang (M2) | M2 | Spec: AC cá bơi 1.5 m/s, phản xạ mép, đổi hướng 120 tick, sinh cá 360 tick (`fish_spawned`, trần 12, 40/30/30), nút N5/N6, `ca_keo`/`keo_neo` | Không | M2.2 |
| 1 | M3.1 | Cao (M3) | M3 | Spec: AC quán v1.1 (2 bếp B1–B2, 4 bàn T1–T4, 6 món), lọc thực đơn theo `day_plan` trong chế độ `day` | Không | M3.2 |
| 1 | M4.1 | Minh (M4) | M4 | Spec: AC vòng ngày `day` (`gather → quan → shop → ngày kế`), Shop (`oxygen`/`hp`, `bought`/`buy_failed`/`shop_end`, `active_upgrades`), Pause (`paused`/`resumed`) | Không | M4.2 |
| 1 | M5.1 | Thanh (M5) | M5 | Spec: danh sách trường snapshot v1.1 cho UI (`monsters[]`, `day`, `day_plan`, `upgrades`, `active_upgrades`, `state:"paused"`), layout Menu/Intro/Result/Summary/Pause/HUD | Không | M5.2 |
| **2** (~1:05–1:20) | M1.2 | Huy (M1) | M1 | Viết unit test/scenario cho Cá Sấu (`patrol`/`chase`/`recoil`, `monster_hit`, bất tử 90 tick, ngất do quái) | M1.1, M6.1 | M1.3 |
| 2 | M2.2 | Quang (M2) | M2 | Viết unit test/scenario cho cá bơi, phản xạ góc/mép, đổi hướng 120 tick, `fish_spawned`, bắt cá kèo & hái kèo nèo | M2.1, M6.1 | M2.3 |
| 2 | M3.2 | Cao (M3) | M3 | Viết unit test/scenario cho 2 bếp, 4 bàn, 6 món và lọc menu theo `day_plan` | M3.1, M6.1 | M3.3 |
| 2 | M4.2 | Minh (M4) | M4 | Viết unit test/scenario cho `day` (1 & nhiều ngày), Shop (`oxygen`/`hp`, hết tiền/max level), Pause ở cả 3 mode | M4.1, M6.1 | M4.3 |
| 2 | M5.2 | Thanh (M5) | M5 | Dựng khung Menu chính, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, Pause overlay trên `chonoi/web/` | M5.1, M6.1 | M5.3 |
| 2 | M6.3 | An (M6) | M6 | Cập nhật `scenario.py` v1.1 (khối `day`, `monsters[]`, `fish[].age_ticks`, cấm `quan.stock`/`quan.reputation` trong `day`, `0 <= money <= earned`) + test | M6.1, M6.2 | Test của M1, M2, M4 |
| **Mốc 1:20** (phút 20) | M6.3b | An + cả nhóm | M6 | **Smoke tích hợp** `gather --inventory-out → quan --inventory` với số chuẩn v1.1, lưu `docs/proof/phase-2/integration.*`; standup 2–3 phút rà lát chậm | M6.1, M6.2 | M6.5 |
| **3** (~1:20–1:38) | M2.3 | Quang (M2) | M2 | Code `gather.py`: cá bơi, phản xạ mép, đổi hướng 120 tick, sinh cá 360 tick (`fish_spawned`), nút N5/N6, bắt `ca_keo` & hái `keo_neo` (**làm trước phần nền `gather.py`**) | M2.2, M6.2 | **M1.3 (Huy)**, M4.3 |
| 3 | M1.3 | Huy (M1) | M1 | Code `gather.py`: Cá Sấu (`M1`, `M2` từ Ngày 3), `patrol`/`chase`/`recoil`, `monster_hit`, rơi 1/2 giỏ LIFO, `invuln_ticks`, `faint cause:"monster"` | M1.2, M6.2, **M2.3 (Quang)** | M4.4, M5.3, M6.4 |
| 3 | M3.3 | Cao (M3) | M3 | Code `quan.py`: hỗ trợ 2 bếp B1–B2, 4 bàn T1–T4, 6 món, tham số lọc `day_plan` từ `day` | M3.2, M6.2 | **M4.3b (Minh)**, M6.4 |
| 3 | M4.3a | Minh (M4) | M4 | Code `runner.py` / `sim/day.py` (hoặc `shop.py`): Pause (`paused`/`resumed`) ở cả 3 mode + logic Shop (`oxygen`/`hp`, `bought`/`buy_failed`/`shop_end`, 600 tick) | M4.2, M6.2 | M4.3b |
| 3 | M4.3b | Minh (M4) | M4 | Ghép vòng ngày `--mode day` (`day_start → day_plan → gather → quan → shop → ngày kế`), chuyển kho trong bộ nhớ, áp `active_upgrades` từ Ngày sau | M4.3a, **M3.3 (Cao)** | M4.4, M5.3, M6.4 |
| 3 | M5.3 | Thanh (M5) | M5 | Hoàn thiện HUD v1.1 trên `chonoi.live`: vẽ Cá Sấu/cá kèo/kèo nèo/2 bếp/4 bàn, cảnh báo `"Thủy quái!"` (viền tím), `"Hết hơi!"`, oxy/kiên nhẫn < 25%, danh sách cần lấy, Shop UI | M5.2, M1.3, M4.3b | M5.4 |
| **4** (~1:38–1:55, cuối phase) | M1.4 | Huy (M1) | M1 | Chạy test Cá Sấu + ngất, lưu bằng chứng vào `docs/proof/phase-2/` | M1.3 | M6.5 |
| 4 | M2.4 | Quang (M2) | M2 | Chạy test cá bơi/sinh + 6 nguyên liệu, lưu bằng chứng vào `docs/proof/phase-2/` | M2.3 | M6.5 |
| 4 | M3.4 | Cao (M3) | M3 | Chạy test 2 bếp/4 bàn/6 món + `day_plan`, lưu bằng chứng vào `docs/proof/phase-2/` | M3.3 | M6.5 |
| 4 | M4.4 | Minh (M4) | M4 | Chạy test `day --days 1` và nhiều ngày (kiểm nâng cấp `oxygen`/`hp` hiệu lực từ Ngày 2) + Pause, lưu bằng chứng | M4.3b, M1.3 | M6.5 |
| 4 | M5.4 | Thanh (M5) | M5 | Chơi thử trọn 1 Ngày trên `chonoi.live` (Menu → Gather → Quan → Shop → Pause), chụp ảnh bằng chứng | M5.3 | M6.5 |
| 4 | M6.4 | An (M6) | M6 | Chạy smoke `day --days 1` & nhiều ngày (≤ 20 s/Ngày), kiểm tất định byte-for-byte, chạy **regression P1** với số chuẩn v1.1 (ghi lý do nếu test P1 đổi theo luật mới) | M1.3, M2.3, M3.3, M4.3b | M6.5 |
| 4 | M6.5 | An (M6, PO) | M6 | Duyệt M1–M5 theo DoD `ticket02.md`, điền `docs/verification/phase-2.md`, họp **retro nhanh 5 phút (1:45–1:50)** và cập nhật `docs/retro.md` | Bằng chứng M1.4–M5.4, M6.4 | M6.6 |
| 4 | M6.6 | An (M6) | M6 | Chạy `check_team.py` + toàn bộ `unittest`, **gắn tag `phase-2` trước 1:55** | M6.5 | — |

## Mở rộng (tùy chọn trong Phase 2 — chỉ làm khi lõi đã xanh)

> Nhóm 6 người cần hoàn thành **ít nhất 2 mục Mở rộng trong cả buổi lab** (khai trong `extensions` của `game.contract.json` và ghi `README.md` kèm bằng chứng). Nếu xong lõi sớm trước 1:35, ưu tiên 2 mục gọn nhất:
> - **M3/M4**: `burn` (Cháy món — `burn_s: 20`, `ready_ticks > 1200` → `dish_burnt`).
> - **M1**: `snake` (Rắn Hổ Mây `M3` — tái dùng trực tiếp logic Cá Sấu với `d ∈ [8, 20]`, chase 3.5 m/s).

## Việc ngoài bảng (mọi người, mọi phase)

| Việc | Khi nào |
|---|---|
| Mỗi người có commit thật (hướng tới ≥ 3 commit có nội dung cả lab), làm chung ghi `Co-authored-by:` | Suốt phase |
| Review chéo: Huy↔Quang (M1↔M2), Cao↔Minh (M3↔M4), Thanh↔An (M5↔M6) | ~1:35–1:42 |
| Cập nhật dòng của mình vào `docs/ai-usage-log.md`, `docs/standup.md`, `docs/members/<handle>.md` | Cuối phase |
| Bị vướng quá 10 phút: báo ngay kênh nhóm để người dự phòng nhận việc | Bất cứ lúc nào |

## Ba điểm dễ nghẽn

1. **M6.1 + M6.2 (Contract v1.1 + CLI/Input/Kho)** phải xong trong **5–10 phút đầu (trước 1:10)**, vì toàn bộ M1–M5 cần cấu hình v1.1 (`6 nguyên liệu`, `6 món`, `day_plan`, `monsters`, `shop`) và cờ `--mode day` / `pause` để chạy test.
2. **Quang (M2.3) và Huy (M1.3) dùng chung `gather.py`**: tách hàm cá bơi/sinh và hàm Cá Sấu thành module helper riêng (ví dụ `chonoi/sim/fish.py`, `chonoi/sim/monsters.py`) rồi chỉ gọi 1 dòng trong `gather.py` để code song song không conflict.
3. **Minh (M4.3b) nối `day` phụ thuộc giao diện `gather` và `quan`**: ngay từ Đợt 2, Minh dựng trước khung `day` + `Shop` bằng fixture cố định, rồi ghép `GatherSim` và `QuanSim` bản v1.1 vào trước **1:35** để kịp chạy smoke `day --days 1` & regression P1.
