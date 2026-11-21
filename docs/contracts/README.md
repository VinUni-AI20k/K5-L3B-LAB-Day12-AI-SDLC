# Hợp đồng tích hợp — Nhóm DoAnhBatDuocEm

> Đã được thống nhất tại kickoff (Thành viên 1 — Integrator hoàn thiện). Mọi thay đổi sau này cần được thông qua nhóm và ghi vào `docs/adr/`.

Tôi hiệu chỉnh phần Gather theo PRD-0 mục E/F/G do người dùng cung cấp ngày 2026-11-21. Lý do và phạm vi được ghi ở [ADR 0001](../adr/0001-gather-prd-payloads.md), để Integrator review trước khi tích hợp. Bảng quán bên dưới chưa nằm trong đợt đối chiếu này.

---

## 1. Schema file kho (`inventory.json`)
* **Khớp mục G của PRD-0:** File kho chỉ chứa duy nhất một khóa gốc `"items"`, bên trong là ánh xạ `{tên_nguyên_liệu: số_nguyên_dương}`. Các mục số lượng bằng 0 sẽ tự động bị loại bỏ khi xuất kho.
* **Các loại nguyên liệu hợp lệ ở Phase 1:**
  - `ca_loc`: Cá lóc
  - `ca_linh`: Cá linh
  - `bong_dien_dien`: Bông điên điển
  - `bong_sung`: Bông súng
* **Nguyên tắc ghi kho:** Ghi nguyên tử qua file tạm `.inv-*.tmp` cùng thư mục; khi có `--inventory-out`, ghi đúng một lần khi `gather_end` với lý do `docked`, `time` hoặc `fainted`. Ngất phải ghi `{"items":{}}`; chưa kết thúc mà chỉ chạm giới hạn `--ticks` thì không tạo hay ghi đè kho.

---

## 2. Giao diện giữa `sim/*` và `client/ui`

### A. Dữ liệu trạng thái UI được đọc (`snapshot`)
* **Chung (`runner.py`):**
  - `tick`, `sim_tick`, `phase_tick`, `mode` (`gather` / `quan`), `phase`, `state` (`playing` / `finished`)
  - `time_left_ticks`, `money`, `earned`, `reputation`, `score`
* **Riêng chế độ `gather` (`chonoi/sim/gather.py`):**
  - `player`: `pos` (`[x, d]`), `vel` (`[vx, vd]`), `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`
  - `hold`: danh sách tên nguyên liệu trong giỏ theo thứ tự nhặt LIFO
  - `hold_count`, `hold_capacity` (12)
  - `nodes`: danh sách nút hái `[{"id", "pos", "kind", "ready", "regrow_ticks"}]`
  - `fish`: danh sách đàn cá `[{"id", "pos", "kind", "heading_deg"}]`
* **Riêng chế độ `quan` (`chonoi/sim/quan.py`):**
  - `player`: `pos` (`[x, z]`)
  - `stock`: từ điển nguyên liệu hiện có trong quán
  - `hand`: món ăn đang cầm trên tay (`None` hoặc tên món)
  - `stoves`: danh sách bếp `[{"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}]`
  - `tables`: danh sách bàn `[{"id", "pos", "customer_id"}]`
  - `customers`: danh sách khách `[{"id", "table_id", "dish", "state", "patience_ticks", "eat_ticks_left", "reserved"}]`

### B. Lệnh điều khiển UI gửi vào (`InputState`)
* `move`: vector hướng 2D `[x, d]` (gather) hoặc `[x, z]` (quan), được chuẩn hóa độ dài <= 1.0.
* `interact`: nút hành động đa năng (E):
  - Ở `gather`: ưu tiên cập bến nếu trong vùng bến; nếu ngoài bến và ở mặt nước thì hái bông.
  - Ở `quan`: tương tác bếp (bắt đầu nấu / nhặt món chín) hoặc tương tác bàn (phục vụ món ăn).
* `catch`: nút bắt cá (Space): chỉ có hiệu lực ở `gather` khi lặn dưới nước và hết hồi chiêu.

---

## 3. Danh sách sự kiện chuẩn (Event Specifications)

### Mode `gather` (Buổi sáng: Lặn & Hái)
| Tên sự kiện | Ý nghĩa | Dữ liệu kèm theo (`data`) |
|---|---|---|
| `dive` | Út Sen chuyển từ mặt nước xuống dưới nước | `{"pos": [x, d]}` |
| `surface` | Út Sen trồi từ dưới nước lên mặt nước | `{"pos": [x, d]}` |
| `oxygen_empty` | Bình oxy vừa giảm từ dương về 0 dưới nước | `{"oxygen_ticks": 0}` |
| `choke` | Bị ngạt nước do hết oxy (mỗi 60 ticks mất 1 HP) | `{"hp": int}` |
| `faint` | Hết máu do ngạt; `lost` là giỏ trước ngất theo thứ tự mới nhất trước, giữ nguyên các phần tử trùng nhau | `{"cause": "choke", "lost": [kind, ...], "hp": 0}` |
| `gather` | Hái bông thành công tại nút | `{"node_id": str, "kind": str, "amount": int}` |
| `hold_full` | Không đủ chỗ nhận toàn bộ yield; giỏ và đối tượng giữ nguyên | `{"action": "gather"\|"catch", "node_id" hoặc "fish_id": str, "required": int, "free": int}` |
| `fish_caught` | Bắt thành công toàn bộ một đàn cá | `{"fish_id": str, "kind": str, "yield": int}` |
| `node_regrown` | Nút bông hoàn tất thời gian hồi sinh | `{"node_id": str}` |
| `gather_end` | Kết thúc phiên lặn | `{"reason": "docked"\|"time"\|"fainted", "inventory": {...}}` |

### Mode `quan` (Buổi tối: Mở Quán Ăn)
| Tên sự kiện | Ý nghĩa | Dữ liệu kèm theo (`data`) |
|---|---|---|
| `customer_arrived` | Khách mới vào quán và được xếp bàn | `{"customer_id": str, "table_id": str, "dish": str}` |
| `no_dish` | Quán không đủ nguyên liệu nấu món nào, khách rời đi | `{"customer_id": str}` |
| `customer_left` | Khách hết kiên nhẫn bỏ về, giảm uy tín | `{"customer_id": str, "reason": "patience_timeout"}` |
| `cook_started` | Bếp bắt đầu nấu món | `{"stove_id": str, "dish": str}` |
| `dish_ready` | Món ăn nấu chín tại bếp | `{"stove_id": str, "dish": str}` |
| `dish_picked` | Người chơi nhặt món ăn từ bếp lên tay | `{"dish": str}` |
| `served` | Người chơi bưng món ăn phục vụ cho bàn khách | `{"table_id": str, "dish": str}` |
| `paid` | Khách ăn xong và thanh toán tiền (+ tip nếu nhanh) | `{"customer_id": str, "money": int, "tip": int}` |
| `quan_end` | Hết giờ ca tối mở quán | `{"reason": "time", "money": int, "earned": int, "reputation": float, "score": int}` |
