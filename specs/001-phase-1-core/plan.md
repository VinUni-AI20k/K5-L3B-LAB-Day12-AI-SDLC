# Implementation Plan: Phase 1 lõi — gather + quan

**Branch**: không tạo (làm trên `tv6/phase-1-team-ai`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-phase-1-core/spec.md`

## Summary

Viết luật Phase 1 trong khung Python có sẵn: `GatherSim.step` (oxy, ngạt, Máu, ngất, hái, bắt cá, giỏ LIFO) và `QuanSim.step` (lịch khách, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, tiền, boa, uy tín). Runner/CLI/kho/JSONL giữ nguyên. Mọi số đọc từ `game.contract.json`, RNG qua `Streams`. Kiểm chứng bằng test headless theo AC-P1-01…23.

## Technical Context

**Language/Version**: Python 3 (chỉ thư viện chuẩn)
**Primary Dependencies**: không; khung `chonoi/` của giảng viên
**Storage**: file JSON (kho `{"items":{}}`), JSONL đầu ra
**Testing**: `unittest` — `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
**Target Platform**: CLI headless + cửa sổ thử `python3 -m chonoi.live`
**Project Type**: CLI mô phỏng tick 60 Hz + client web tĩnh
**Performance Goals**: 10 800 tick/buổi < 5 s
**Constraints**: tất định từng byte; số liệu chỉ từ contract; không `random` toàn cục/đồng hồ; sắp `sort_by_id`, id qua `IdAllocator`
**Scale/Scope**: 2 file luật (~300–400 dòng), 1 file UI, test mới trong `tests/`

## Constitution Check

| Nguyên tắc | Đánh giá |
|---|---|
| I. Contract-First | ĐẠT — hằng số đọc `self.t[...]`, `self.menu`; không sửa `game.contract.json` |
| II. Deterministic | ĐẠT — chọn món qua `self.rng.get("quan_order")`; duyệt theo `sort_by_id` |
| III. Headless-First | ĐẠT — mọi AC kiểm qua `chonoi.headless`; không có sáng tạo ở P1 |
| IV. Test-First & Evidence | ĐẠT — mỗi AC có task test (TV5) + ma trận `docs/verification/phase-1.md` |
| V. No Invented Requirements | ĐẠT phần lớn — số chuẩn đã xác nhận bởi TICKET-02 (boa floor, `order_tick`, ngạt, lịch 120+900k, đóng ca); còn GIẢ ĐỊNH: `data` event v1.0, thứ tự bước quán, cá bị bắt bị loại |
| VI. Small Slices | ĐẠT — 4 lát luật (TV1–TV4), mỗi lát một nhóm hàm riêng |

Re-check sau thiết kế: không vi phạm mới.

## Project Structure

### Documentation

```text
specs/001-phase-1-core/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md · tasks.md · analysis.md
├── checklists/requirements.md
└── contracts/{events.md, sim-ui.md}
```

### Source Code

```text
chonoi/
├── sim/gather.py     # TV1 (lát 1: _update_zone/_update_oxygen/_choke_faint, giỏ) · TV2 (lát 2: _try_gather/_try_catch)
├── sim/quan.py       # TV3 (lát 3: lịch khách, giữ chỗ, kiên nhẫn, no_dish) · TV4 (lát 4: _interact, bếp, bưng, paid, boa)
├── scenario.py       # TODO(nhóm) kiểm mâu thuẫn mức luật — CẦN NHÓM ĐỒNG Ý (file khung)
└── web/index.html    # TV6 / worker Cursor: HUD đọc trường mới
tests/
└── test_p1_rules.py  # TV5: test theo AC (mới; không sửa smoke có sẵn)
docs/verification/phase-1.md, docs/proof/phase-1/   # TV5
```

**Structure Decision**: giữ nguyên starter; chia hàm riêng trong mỗi file để 2 người cùng file ít conflict.

## Thiết kế chính

### Gather — `step()` (FR-012)
1. đồng hồ/bộ đếm/mọc lại (đã có)
2. `was_surface = _at_surface()`; `_move(inp)` (đã có)
3. `_update_zone(was_surface)` → dive/surface; `_update_oxygen()` → oxygen_empty, choke, faint; nếu faint: `hold=[]`, `_finish("fainted")`, return
4. `interact`: `_in_dock()` → docked (đã có); else nếu `_at_surface()` → `_try_gather()`
5. `catch`: nếu không ở mặt nước và cd == 0 → `_try_catch()`
6. hết giờ (đã có)

Hàm chung: `_nearest(coll, radius)` = min theo `(dist, id)`; `_add_to_hold(kind, count) -> bool` (tất cả hoặc không).

### Quan — `step()` (FR-022)
1. đồng hồ; `_tick_customers()` (kiên nhẫn ↓ → customer_left; eating ↓ → paid) và `_tick_stoves()` (cooking ↓ → dish_ready), theo id
2. `_move(inp)` (đã có)
3. nếu `interact`: `_interact()` — ứng viên = bếp/bàn trong `interact_radius` có hành động hợp lệ, khóa `(dist, 0|1, id)`, làm đúng một
4. `_spawn_if_due()` — so `sim_tick` với lịch; bàn trống id nhỏ; `_cookable()` trừ giữ chỗ; `no_dish` hoặc `customer_arrived`
5. hết giờ (đã có)

Hằng: `ticks(x_s) = round(x_s * tuning["tick_hz"])`. Cần biến đếm tick nội bộ `self.tick` (sim không nhận tick từ runner). Khách xuất tập trường cố định (`dish_id`, `patience_ticks_left`, `eat_ticks_left` — khớp HUD). Uy tín `round(x, 6)` sau mỗi thay đổi.

### Contracts
- Sự kiện: [contracts/events.md](contracts/events.md) — TV1 chép phần đã chốt sang `docs/contracts/`.
- Sim ↔ UI: [contracts/sim-ui.md](contracts/sim-ui.md).
- Kho: Contract G có sẵn, không đổi.

## Complexity Tracking

| Vi phạm | Vì sao | Phương án đơn giản bị loại |
|---|---|---|
| Có thể sửa `chonoi/scenario.py` (file khung) cho AC-P1-23 (Q-F) | Starter để `TODO(nhóm)` ở đó | Kiểm trong `QuanSim.__init__` raise `BadInput` — an toàn vì `runner.run` dựng `Session` (dòng 78) **trước** khi mở `JsonlWriter` (dòng 80), nên mã 2 không để lại file `--out`. **Ưu tiên phương án này** nếu nhóm không muốn đụng khung |
