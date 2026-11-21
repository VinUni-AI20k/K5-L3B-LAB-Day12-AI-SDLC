# Hợp đồng Tích hợp — Nhóm 05 (PRD-0 Phase 1)

Đã chốt trước T+15 cho toàn bộ 5 thành viên.

---

## 1. Schema File Kho (`--inventory-out` và `--inventory`)

Khớp mục G của PRD-0 và Test Contract v1.0.

```json
{
  "items": {
    "bong_dien_dien": 1,
    "bong_sung": 2,
    "ca_linh": 3,
    "ca_loc": 1
  }
}
```

- **Quy tắc:**
  - Chỉ có duy nhất một khóa gốc `"items"`.
  - Khóa con chỉ nằm trong 4 nguyên liệu hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
  - Giá trị là số nguyên không âm (`int >= 0`). Nếu số lượng bằng 0 thì lược bỏ khi ghi ra file.
  - File kho rỗng biểu diễn là `{"items": {}}`.
  - File mẫu hợp lệ: `docs/contracts/inventory.sample.json`.
- **Hành vi I/O:**
  - **Gather:** Chỉ tạo file `--inventory-out` khi `gather_end` (`docked`, `time`, `fainted`). Khi ngất (`fainted`), kho xuất ra là rỗng (`{"items": {}}`). Nếu hết `--ticks` trước khi kết thúc ca (`tick_limit`), tuyệt đối không tạo/ghi đè file kho. Ghi file nguyên tử (atomic write qua file tạm cùng thư mục).
  - **Quán:** Đọc file kho từ `--inventory`. Nếu sai schema hoặc chứa nguyên liệu lạ, chương trình lập tức thoát với mã 2 (`BadInput`). Nếu không truyền `--inventory` và không có scenario stock, khởi tạo kho rỗng.

---

## 2. Giao diện Input & Snapshot (Client / HUD / Simulator)

### Input từ Player (`POST /input` hoặc file JSON inputs)
- `move`: `[x, d]` (gather: d > 0 là bơi xuống) hoặc `[x, z]` (quan), các thành phần thuộc `[-1.0, 1.0]`.
- `interact`: `bool` (cạnh lên: ưu tiên bến, hái nút sẵn sàng ở mặt nước; ở quán: thao tác bếp/bàn gần nhất).
- `catch`: `bool` (cạnh lên: bắt đàn cá trong tầm khi ở dưới nước).

### Snapshot State (Chế độ chỉ đọc cho Client/HUD)
- **Gather (`sim.mode == 'gather'`):**
  - `player`: `pos` [x, d], `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `at_surface`.
  - `hold`: danh sách nguyên liệu trong giỏ theo thứ tự nhặt (LIFO), `hold_count`, `hold_capacity`.
  - `nodes`: danh sách nút hái `[id, kind, pos, ready, regrow_ticks]`.
  - `fish`: danh sách đàn cá `[id, kind, pos, heading_deg]`.
- **Quán (`sim.mode == 'quan'`):**
  - `player`: `pos` [x, z].
  - `stock`: nguyên liệu vật lý khả dụng.
  - `hand`: món ăn đang bưng trên tay (`dish_id` hoặc `null`).
  - `stoves`: `[id, pos, state, dish, cook_ticks_left, ready_ticks]`.
  - `tables`: `[id, pos, customer_id]`.
  - `customers`: `[id, table_id, dish, patience_ticks, state, reserved]`.

---

## 3. Danh sách Sự kiện (Events)

### A. Chế độ Gather (`sim/gather.py`)
| Tên Event | Payload `data` | Thời điểm phát | Phụ trách |
|---|---|---|:---:|
| `dive` | `{"pos": [x, d]}` | Vừa chuyển từ mặt nước xuống dưới nước | TV1 |
| `surface` | `{"pos": [x, d]}` | Vừa trồi từ dưới nước lên mặt nước | TV1 |
| `oxygen_empty` | `{}` | Oxy giảm từ $> 0$ xuống $0$ dưới nước | TV1 |
| `choke` | `{"hp": int}` | Đủ `choke_interval_ticks` khi oxy = 0 $\to$ trừ 1 HP | TV1 |
| `faint` | `{}` | HP về 0 $\to$ ngất, giỏ bị xoá sạch | TV1 |
| `node_regrown`| `{"node_id": str}` | Đếm lùi `regrow_ticks` về 0 | TV2 |
| `gather` | `{"node_id": str, "kind": str, "count": int}` | Hái thành công bông súng/điên điển | TV2 |
| `hold_full` | `{"kind": str}` | Giỏ không đủ chỗ chứa sản lượng | TV2 |
| `fish_caught` | `{"fish_id": str, "kind": str, "count": int}` | Bắt thành công đàn cá dưới nước | TV2 |
| `gather_end` | `{"reason": "docked"\|"time"\|"fainted", "inventory": dict}` | Kết thúc buổi sáng | TV1 / TV2 |

### B. Chế độ Quán (`sim/quan.py`)
| Tên Event | Payload `data` | Thời điểm phát | Phụ trách |
|---|---|---|:---:|
| `customer_arrived` | `{"customer_id": str, "dish": str, "table_id": str, "patience_ticks": int}` | Khách đến, ngồi vào bàn trống | TV3 |
| `no_dish` | `{"customer_id": str}` | Không có món nào đủ nguyên liệu | TV3 |
| `customer_left` | `{"customer_id": str, "reason": "impatient"}` | Hết kiên nhẫn bỏ về, trừ uy tín | TV3 |
| `cook_started` | `{"stove_id": str, "dish": str}` | Bắt đầu nấu món tại bếp trống | TV4 |
| `dish_ready` | `{"stove_id": str, "dish": str}` | Nấu xong sau `cook_s` | TV4 |
| `dish_picked` | `{"stove_id": str, "dish": str}` | Bốc món chín lên tay | TV4 |
| `served` | `{"table_id": str, "dish": str}` | Đặt món lên bàn cho khách | TV4 |
| `paid` | `{"customer_id": str, "dish": str, "price": int, "tip": int}` | Khách ăn xong trả tiền + tip | TV4 |
| `quan_end` | `{"reason": "time", "money": int, "earned": int, "shift_earned": int, "reputation": float}` | Hết ca buổi tối | TV4 |
