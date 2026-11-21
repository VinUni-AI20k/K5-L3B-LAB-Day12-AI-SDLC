# Hợp đồng tích hợp

Nguồn: PRD-0 mục C, E, G; Contract v1.1 (Phase 2) mục 1.1, 4.3–4.5. Khi đổi hợp đồng: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú).

## 1. File kho (gather → quan, PRD-0 mục G)

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Chỉ có khóa gốc `items`, là object `kind → số nguyên > 0`. Kind vắng tính là 0; bên ghi bỏ các khóa có lượng 0. Kho rỗng ghi là `{"items":{}}`.
- Kind hợp lệ (v1.1, 6 loại): cá `ca_linh`, `ca_loc`, `ca_keo`; cây `bong_dien_dien`, `bong_sung`, `keo_neo` (khai ở `chonoi/inventory.py`). Sai schema, kind lạ hoặc số âm thì bên đọc thoát mã 2.
- **Bên ghi** (gather, `--inventory-out`): ghi đúng một lần khi có `gather_end`, nội dung khớp `gather_end.data.inventory`. Ngất thì ghi kho rỗng. Chạm `--ticks` trước khi buổi sáng kết thúc thì không tạo và không ghi đè file. Ghi qua file tạm rồi thay thế nguyên tử.
- **Bên đọc** (quan, `--inventory`): kho thành `stock` ở snapshot tick 0. Trần giỏ không áp lên kho quán. Không được khai cùng lúc `--inventory` và `scenario.quan.stock`.
- Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json). Kho thật lấy từ một lượt thu: [`docs/proof/phase-1/kho.json`](../proof/phase-1/kho.json).
- Mode `day` (v1.1) sẽ tự bàn giao cùng schema này trong bộ nhớ. **Chưa làm:** `--mode day` hiện vẫn thoát mã 2 và `contract_version` vẫn là `"1.0"` (Integrator quyết khi nâng). Hai cờ file kho chỉ dùng cho hai mode độc lập.
- Kiểm bàn giao: `python3 tools/check_handoff.py <gather.jsonl> <kho.json>` (mã 0 là khớp, 1 là lệch). Danh sách loại đọc từ `game.contract.json`.

## 2. Giao diện `sim/*` ↔ `client/ui`

UI (`chonoi/live.py`, `chonoi/web/`) **chỉ đọc snapshot**, không đọc hay sửa trạng thái bên trong sim. UI gửi vào đúng một `InputState` mỗi tick.

| Chiều | Gather | Quan |
|---|---|---|
| UI → sim | `move [x, d]`, `interact` (E), `catch` (Space); nút chỉ có tác dụng ở cạnh lên | `move [x, z]`, `interact` (E) |
| sim → UI (snapshot) | `player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold`, `hold_count`, `hold_capacity`, `nodes[]{id, pos, kind, ready, regrow_ticks}`, `fish[]{id, pos, kind, heading_deg, age_ticks}` | `player`, `stock`, `hand`, `stoves[]`, `tables[]`, `customers[]` (PRD-0 mục D/E) |
| Chung | `tick`, `phase`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score` | như cột Gather |

## 3. Sự kiện

Event ghi ở tick k+1 cho bước k, theo thứ tự xử lý. Người nghe: UI/HUD (hiển thị), test/QA (kiểm chứng), runner (chỉ `gather_end`).

**Gather** (phát trong `chonoi/sim/gather.py`)

| name | data | Lát phát |
|---|---|---|
| `node_regrown` | `node_id` | 2 |
| `gather` | `node_id`, `kind`, `amount` | 2 |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required`, `free` | 2 |
| `fish_caught` | `fish_id`, `kind`, `yield` | 2 |
| `dive` / `surface` | `pos` sau khi di chuyển, chỉ phát khi đổi phía mặt nước | 1 |
| `oxygen_empty` / `choke` | `oxygen_ticks: 0` / `hp` sau khi trừ | 1 |
| `faint` | `cause: "choke"`, `lost` (mảng kind, LIFO), `hp: 0` | 1 |
| `fish_spawned` | `id`, `kind`, `pos` khi sinh theo lịch (phase_tick = 360·k); đàn đầu ca không phát | 2 (P2) |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` (object theo mục 1) → runner ghi file kho | 2 (khung) |

**Quan** (phát trong `chonoi/sim/quan.py`; lát 3 và lát 4 xác nhận lại)

| name | data |
|---|---|
| `customer_arrived` / `no_dish` | `order_id`, `table_id`, `dish_id` / `{}` |
| `cook_started` | `stove_id`, `order_id`, `dish_id`, `items` (mảng kind, sắp theo kind), `base_price` |
| `dish_ready` / `dish_picked` | `stove_id`, `order_id`, `dish_id` |
| `served` | `order_id`, `table_id`, `dish_id`, `patience_ticks_left`, `base_price`, `tip` |
| `paid` | `order_id`, `table_id`, `base_price`, `tip`, `amount`, `reason` (`finished_eating`/`closing`) |
| `customer_left` | `order_id`, `table_id`, `reason` (`patience`/`closing`), `reputation` |
| `quan_end` | `reason: "time"`, `money`, `earned`, `shift_earned`, `reputation` |
