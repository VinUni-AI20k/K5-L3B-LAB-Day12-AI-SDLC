# Hợp đồng tích hợp — Nhom456 (Phase 1 / Contract v1.0)

> Thống nhất bởi Integrator (`nlamtung`) & toàn nhóm dựa trên **PRD-0 — Test Contract v1.0**. Khi thay đổi hợp đồng sau này, báo trên Zalo và ghi ADR trong `docs/adr/`.

## 1. Schema file kho (`gather` → `quan`, mục G)

- Đường dẫn mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Chỉ có đúng một khóa gốc `"items"`: object ánh xạ `kind -> số nguyên không âm`.
- 4 nguyên liệu Phase 1: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Nguyên liệu vắng coi là `0`; bên ghi bỏ mọi khóa có lượng `0` (kho rỗng là `{"items":{}}`).
- Bên ghi (`gather --inventory-out`): ghi **đúng một lần** qua file tạm + thay thế nguyên tử khi có `gather_end` (ngất `fainted` ghi rỗng); dừng do `--ticks` không tạo/ghi đè file.
- Bên đọc (`quan --inventory`): sai schema, kind lạ hoặc giá trị âm → thoát mã `2` trước khi ghi output.

## 2. Giao diện giữa `sim/*` và `client/ui`

- Dùng chung `chonoi.runner.Session` (60 tick/s), UI **không** nhân đôi logic mô phỏng.
- **UI → Sim (`POST /input` / `InputState`):** `{"move": [a, b], "interact": bool, "catch": bool}` (nút kích hoạt theo cạnh lên `false -> true`; `gather`: `[x, d]` với `+d` là xuống; `quan`: `[x, z]` với `+z` là bắc) và `POST /restart`.
- **Sim → UI (`GET /state` / `Session.snapshot()`):**
  - Chung: `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
  - `gather`: `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`), `hold`, `hold_count`, `hold_capacity`, `nodes[]` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish[]` (`id`, `pos`, `kind`, `heading_deg`).
  - `quan`: `player` (`pos`), `stock`, `hand` (payload món `{order_id, dish_id, base_price}` hoặc `null`), `stoves[]` (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`), `tables[]` (`id`, `pos`, `customer_id`), `customers[]` (`id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip`).

## 3. Danh sách sự kiện (mục E)

| Pha | Tên sự kiện (`name`) | Cấu trúc `data` | Bên phát / Bên nghe |
|---|---|---|---|
| `gather` | `node_regrown` | `{"node_id"}` | `sim/gather` → JSONL, UI |
| `gather` | `dive` / `surface` | `{"pos": [x, d]}` (sau di chuyển, khi đổi phía biên `surface_depth`) | `sim/gather` → JSONL, UI |
| `gather` | `oxygen_empty` | `{"oxygen_ticks": 0}` (khi oxy từ dương xuống 0) | `sim/gather` → JSONL, UI |
| `gather` | `choke` | `{"hp"}` (HP sau khi trừ 1) | `sim/gather` → JSONL, UI |
| `gather` | `faint` | `{"cause": "choke", "lost": [...], "hp": 0}` (`lost` theo thứ tự LIFO) | `sim/gather` → JSONL, UI |
| `gather` | `gather` | `{"node_id", "kind", "amount"}` | `sim/gather` → JSONL, UI |
| `gather` | `fish_caught` | `{"fish_id", "kind", "yield"}` | `sim/gather` → JSONL, UI |
| `gather` | `hold_full` | `{"action": "gather"\|"catch", "node_id"\|"fish_id", "required", "free"}` | `sim/gather` → JSONL, UI |
| `gather` | `gather_end` | `{"reason": "time"\|"docked"\|"fainted", "inventory": {"items": {...}}}` | `sim/gather` → JSONL, runner (ghi kho), UI |
| `quan` | `customer_arrived` | `{"order_id", "table_id", "dish_id"}` | `sim/quan` → JSONL, UI |
| `quan` | `no_dish` | `{}` (có bàn trống nhưng không đủ nguyên liệu cho món nào) | `sim/quan` → JSONL, UI |
| `quan` | `cook_started` | `{"stove_id", "order_id", "dish_id", "items": [...], "base_price"}` (`items` sắp theo `kind`) | `sim/quan` → JSONL, UI |
| `quan` | `dish_ready` | `{"stove_id", "order_id", "dish_id"}` | `sim/quan` → JSONL, UI |
| `quan` | `dish_picked` | `{"stove_id", "order_id", "dish_id"}` | `sim/quan` → JSONL, UI |
| `quan` | `served` | `{"order_id", "table_id", "dish_id", "patience_ticks_left", "base_price", "tip"}` | `sim/quan` → JSONL, UI |
| `quan` | `paid` | `{"order_id", "table_id", "base_price", "tip", "amount", "reason": "finished_eating"\|"closing"}` | `sim/quan` → JSONL, UI |
| `quan` | `customer_left` | `{"order_id", "table_id", "reason": "patience"\|"closing", "reputation"}` | `sim/quan` → JSONL, UI |
| `quan` | `quan_end` | `{"reason": "time", "money", "earned", "shift_earned", "reputation"}` | `sim/quan` → JSONL, UI |
