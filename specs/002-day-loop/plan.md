# Implementation Plan: Phase 2 — day loop (Test Contract v1.1)

**Branch**: không tạo (làm trên `tv6/phase-1-team-ai`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

## Summary
Ưu tiên tuyệt đối là hoàn tất lõi P1 (hái, bắt cá, toàn bộ quán) với số chuẩn. Sau đó: contract v1.1 + cá bơi/sinh (lát 1), Cá Sấu (lát 2), quán 2 bếp/4 bàn/6 món + `day_plan` (lát 3), `--mode day` + Shop + pause (lát 4), UI cho Cursor. Mọi số lấy từ `game.contract.json` v1.1, RNG qua `Streams`.

## Technical Context
**Language**: Python 3, chỉ thư viện chuẩn · **Testing**: `unittest` (`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`)
**Project**: CLI headless 60 Hz + client web tĩnh (`chonoi/web/`, `chonoi.live`)
**Performance**: 1 Ngày (≤ 22 200 tick) ≤ 20 s headless; UI ≥ 30 FPS ở 1280×720
**Constraints**: tất định từng byte; không hard-code số; `sort_by_id`; `IdAllocator` cho cá sinh thêm
**Scope**: `chonoi/sim/{gather,quan}.py` + mới `chonoi/sim/{fish,monsters,day,shop}.py`; sửa có kiểm soát file khung (xem dưới)

## Constitution Check
| Nguyên tắc | Đánh giá |
|---|---|
| I. Contract-First | ĐẠT — TV1 cập nhật `game.contract.json` v1.1 + `docs/contracts/` trước khi các lát dùng số mới |
| II. Deterministic | ĐẠT — luồng `fish_turn`, `fish_spawn`, `quan_order`; duyệt theo id |
| III. Headless-First | ĐẠT — mọi AC qua headless; UI chỉ đọc snapshot; mở rộng hoãn |
| IV. Test-First & Evidence | ĐẠT — TV5 viết test theo AC-P2, regression P1, `docs/proof/phase-2/` |
| V. No Invented Requirements | ĐẠT phần lớn — bản đề đầy đủ đã chốt chuỗi bị cắt; còn GIẢ ĐỊNH: `faint` do ngạt (#30), `extensions` (#32), cá bị loại (#33), tên luồng RNG |
| VI. Small Slices | CÓ ĐIỀU KIỆN — lát 4 đụng nhiều file khung → tách task nhỏ, một chủ mỗi file |

**Vi phạm cần chấp nhận** (Complexity Tracking): sửa file khung.

## Project Structure
```text
specs/002-day-loop/  spec · plan · research · data-model · quickstart · tasks · analysis · contracts/{events-v1.1, cli-inputs-v1.1}.md
chonoi/
├── sim/gather.py    # P0 TV2: hái + bắt cá; TV1: gọi fish.py; TV2: gọi monsters.py
├── sim/fish.py      # MỚI — TV1: bơi, đổi hướng, phản xạ, sinh
├── sim/monsters.py  # MỚI — TV2: patrol/chase/recoil, hit, rơi LIFO
├── sim/quan.py      # P0 TV3+TV4: lõi quán; sau đó 2 bếp/4 bàn/6 món, lọc day_plan, order_tick
├── sim/day.py       # MỚI — TV6(+TV5): máy trạng thái pha, bàn giao kho, cấp hiệu lực
├── sim/shop.py      # MỚI — TV6: buy/shop_done/600 tick
├── headless.py      # KHUNG — TV6: --mode day, --days
├── inputs.py        # KHUNG — TV6: pause, shop_done, buy (chuỗi, không kế thừa)
├── runner.py        # KHUNG — TV6: pause (tick vs sim_tick vs phase_tick), đổi pha, vỏ event `day`, end.days_completed
├── live.py          # KHUNG — TV6: --mode day, input pause/shop_done/buy, meta theo pha + menu/day_plan/shop
├── scenario.py      # KHUNG — TV6: khối day, gather.monsters, fish.age_ticks, cấm quan.stock trong day
├── contract.py      # KHUNG — TV1: validate v1.1
├── inventory.py     # KHUNG — TV1: 6 nguyên liệu
└── web/             # Cursor (chủ TV6): menu, màn chuyển, pause, Shop, HUD mới
game.contract.json, docs/contracts/   # TV1
tests/test_p2_*.py, docs/proof/phase-2/, docs/verification/phase-2.md   # TV5
```

## Thiết kế chính
- **Day runner**: `DaySession` giữ `DayState`; mỗi pha dựng sim con (`GatherSim(day_ctx)`, `QuanSim(day_ctx, inventory=...)`, `ShopSim`). Khi sim con `done`: phát event kết thúc (pha cũ), dựng pha mới, phát `phase_start` cùng tick, snapshot pha mới `phase_tick:0`. Pha mới chạy từ bước sau.
- **Pause**: xét trước mọi thứ trong bước; nếu vào/đang pause: `tick += 1`, không gọi `sim.step`, bỏ cạnh hành động; cạnh `pause` kế → `resumed` rồi chạy `sim.step` ngay bước đó. `Session.step` cần tách `tick`/`sim_tick`/`phase_tick` (hiện runner dùng chung `self.tick`).
- **Gather step v1.1**: đồng hồ/cd/bất tử/nút → bơi, oxy, ngạt (Máu 0 → faint+end, return) → quái theo id, tối đa 1 hit → interact (bến trước hái) → catch (vị trí cá trước bơi) → hết giờ → nếu chưa xong: cá bơi, sinh.
- **Cá**: miền x `fish_x`, d `fish_depths[kind]`; phản xạ: `p' = 2·mép − p`, đảo thành phần hướng; `heading_deg` cập nhật theo vector.
- **Quái**: một hàm `update_monster(m, player)` theo state; hit chọn `min((dist, id))` trong `hit_radius`.
- **Shop**: `buy` xử lý trước `shop_done` trong cùng bước; `time_left_ticks` 600 giảm chỉ khi không pause.
- **Cấp hiệu lực**: `oxygen_max_s`, `hp_max` lấy từ `shop.upgrades[*][active_level-1]`, mặc định tuning gather.

## Complexity Tracking
| Vi phạm | Vì sao | Phương án đơn giản bị loại |
|---|---|---|
| Sửa 7 file khung (`headless, inputs, runner, scenario, live` — TV6; `contract, inventory` — TV1) + sửa test cũ (TV5) | Test Contract v1.1 bắt buộc `--mode day`, `--days`, nút mới, 6 nguyên liệu; khung hiện từ chối `day` | Entry point riêng: vẫn phải chạy qua `headless_cmd` và cùng validate → không tránh được. Giảm rủi ro: mỗi file một chủ, báo nhóm, ghi lý do commit |
