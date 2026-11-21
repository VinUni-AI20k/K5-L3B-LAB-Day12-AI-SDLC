# Kế hoạch Phase 2 — TICKET-02 "Một ngày ở chợ nổi" (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.1 (`contract_version: "1.1"`, số chuẩn, 6 nguyên liệu, 6 món), cá bơi/sinh, Cá Sấu + Máu/ngất, 2 bếp/4 bàn, `--mode day` (D1–D5, Shop, nâng cấp oxygen/hp), menu + pause + HUD. Tag `phase-2` trước 1:55.

## Chia lát (giữ chủ file như Phase 1 để khỏi block nhau)
| Lát | Phạm vi (theo ticket) | Người | File chính |
|---|---|---|---|
| 1. Số chuẩn + cá | §1.1, §4.1 khóa gather; cá bơi, đổi hướng, sinh theo lịch, N5/N6, `ca_keo`/`keo_neo` | NguyenQuangDunghe161764 (cá) + invzble-z (số liệu `game.contract.json`) | `sim/gather.py` (phần cá), `game.contract.json` |
| 2. Cá Sấu, Máu, ngất | §1.2: patrol/chase/recoil, hit + bỏ nửa giỏ LIFO, bất tử 90 tick, `monster_hit`, `faint.cause` | comtrang378-ship-it | `sim/monsters.py` (mới), hàm Máu/ngất trong `gather.py` |
| 3. Quán 2 bếp/4 bàn | §1.3: B2, T2–T4, 6 món, lịch khách 120+900k, lọc món theo kế hoạch | Quoosc (khách) + ttkien0710 (bếp/món) | `sim/quan.py` |
| 4a. Vòng ngày + Shop (sim) | §2, §4.2–4.5: `--mode day`, `--days`, đổi pha, Shop/buy/shop_done, pause, `day_plan`, `active_upgrades` | invzble-z | `sim/day.py` (mới), `runner.py`, `headless.py`, `inputs.py` |
| 4b. Menu, intro, pause, HUD, Shop UI | §2 "Menu, pause và HUD" | nganhduong123 | `chonoi/web/`, `chonoi/live.py` |
| QA | smoke tích hợp (phút 20), smoke `day --days 1`, regression P1 với số chuẩn (ghi lý do đổi test), verification | WorkOfMinh | `tests/`, `docs/proof/phase-2/`, `docs/verification/phase-2.md` |

## Giao diện cần chốt ở phút 0–5 (ghi vào `docs/contracts/`)
- `DaySim` giữ `GatherSim`/`QuanSim`/Shop hiện tại, bàn giao kho trong bộ nhớ theo schema kho v1.0.
- Input: `pause`, `shop_done` (boolean, cạnh lên), `buy` (chuỗi, chỉ ở frame khai báo). Sim đọc `inp.pressed("pause")`, `inp.buy`.
- Snapshot day: `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase` ∈ gather/quan/shop, `state:"paused"`; gather thêm `monsters[]`.
- Trường khách trong snapshot quán (UI đang giả định `table_id`, `dish_id`, `state`, `patience_ticks_left`, `reserved`).

## Mốc giờ
- 0–5: chốt giao diện trên. · 5–20: làm 4 lát. · 20: smoke `gather --inventory-out` → `quan --inventory`, lưu `docs/proof/phase-2/integration.*`, standup.
- 20–35: tích hợp `day`. · 35–45: smoke `day --days 1`, nhiều Ngày, regression P1, verification, tag. · 45–50: retro. · 50–55: dự phòng.

## Rủi ro
- Lát 4a là đường găng (UI pause/Shop phụ thuộc). UI dùng mock (`/?mock=day-shop`...) để không phải chờ.
- Nhóm 7 người: số mục mở rộng bắt buộc chưa rõ (xem `docs/clarify.md` #2). Chỉ làm sau khi lõi xanh.
