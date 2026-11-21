# Giao diện `client/ui` ↔ `sim/*` trên `chonoi.live` (Task M5.2)

> Phụ trách: **M5 — Vũ Quang Thanh (`thanhvu101`)**  
> Tham chiếu hợp đồng gốc: [`docs/contracts/README.md`](contracts/README.md) và `PRD0.md` (mục C, D, E, F).

Tài liệu này quy định đầy đủ danh sách **lệnh UI gửi vào máy chủ** và **trường dữ liệu UI đọc từ snapshot** cho cả hai chế độ `gather` (buổi sáng — Lặn & Hái) và `quan` (buổi tối — Mở Quán trên nhà bè).

---

## 1. Lệnh UI gửi lên máy chủ (`chonoi.live`)

Máy chủ HTTP `chonoi.live` nhận hai lệnh điều khiển từ trình duyệt:

### 1.1. `POST /input` — Cập nhật trạng thái phím điều khiển
- **Content-Type**: `application/json`
- **Payload chuẩn**:
  ```json
  {
    "move": [0, 1],
    "interact": false,
    "catch": false
  }
  ```
- **Ràng buộc & quy ước trục tọa độ**:
  | Trường | Kiểu | Miền hợp lệ | Phím trên UI | Quy ước theo chế độ (`mode`) |
  |---|---|---|---|---|
  | `move` | `[number, number]` | Mỗi phần tử $\in [-1, 1]$ (sim chuẩn hóa nếu độ dài $> 1$) | `W/A/S/D` hoặc Phím mũi tên | - **`gather` (`[x, d]`)**: `move[0] > 0` sang phải (đông); **`move[1] > 0` bơi xuống sâu (`+d`)** (`S` / `ArrowDown` $\rightarrow +1$, `W` / `ArrowUp` $\rightarrow -1$).<br>- **`quan` (`[x, z]`)**: `move[0] > 0` sang phải (đông); **`move[1] > 0` đi lên hướng bắc (`+z`)** (`W` / `ArrowUp` $\rightarrow +1$, `S` / `ArrowDown` $\rightarrow -1$). |
  | `interact` | ` boolean` | `true` \| `false` | Phím `E` | Chỉ kích hoạt trong `sim` ở **cạnh lên** (`false` $\rightarrow$ `true`).<br>- **`gather`**: Xét cập bến trước (`docked`), ngoài bến và ở mặt nước ($d \le 0.5$) thì hái nút `ready` gần nhất.<br>- **`quan`**: Chọn tối đa 1 đối tượng trong `interact_radius` theo thứ tự ưu tiên `(khoảng cách, bếp trước bàn, id)` để nấu (`idle` $\rightarrow$ `cooking`), bưng (`ready` $\rightarrow$ `hand`), hoặc phục vụ bàn (`hand` $\rightarrow$ `eating`). |
  | `catch` | `boolean` | `true` \| `false` | Phím `Space` | Chỉ kích hoạt ở **cạnh lên** (`false` $\rightarrow$ `true`) trong chế độ **`gather`** khi đang ở dưới nước ($d > 0.5$) và `catch_cd_ticks == 0`. Ở chế độ `quan` được bỏ qua. |

- **Xử lý mất tiêu điểm (`blur`)**: Khi cửa sổ trình duyệt mất focus, UI tự động gửi `{"move": [0, 0], "interact": false, "catch": false}` để nhân vật không bị kẹt phím.

### 1.2. `POST /restart` — Chơi lại lượt hiện tại
- **Payload**: `{}` (hoặc rỗng)
- **Phím trên UI**: Phím `R` (hoặc nút trên màn hình).
- **Hành vi**: Khởi tạo lại `Session` với cùng `mode`, `seed`, `tuning`, `scenario` và `inventory` ban đầu.

---

## 2. Trường dữ liệu UI đọc từ máy chủ (`GET /state`)

UI poll `GET /state` (chu kỳ ~16 ms) và nhận về một JSON object gồm toàn bộ trường của `snapshot` chuẩn (theo `PRD0.md` mục E) cộng thêm các trường bao ngoài của `LiveGame`:

### 2.1. Trường chung cho mọi chế độ (`gather` & `quan`)

| Tên trường | Kiểu | Nguồn | Ý nghĩa & cách hiển thị trên HUD |
|---|---|---|---|
| `type` | `"snapshot"` | `runner.Session` | Định danh bản ghi snapshot chuẩn. |
| `tick` | `int` | `runner.Session` | Bước thời gian ngoài hiện tại (60 tick = 1 giây). |
| `sim_tick` | `int` | `runner.Session` | Tổng số bước gameplay đã chạy. |
| `mode` | `"gather" \| "quan"` | `runner.Session` | Chế độ đang chạy; quyết định nhánh render `drawGather()` hoặc `drawQuan()`. |
| `phase` | `"gather" \| "quan"` | `runner.Session` | Pha hiện tại của lượt chơi. |
| `phase_tick` | `int` | `runner.Session` | Số tick đã chạy trong pha hiện tại (dùng cho lịch khách ở `quan`). |
| `state` | `"playing" \| "finished"` | `runner.Session` | Trạng thái lượt chơi. |
| `time_left_ticks` | `int` | `sim` | Thời gian còn lại của ca (quy đổi `Math.ceil(time_left_ticks / 60)` ra `MM:SS` trên HUD). |
| `money` | `int` | `sim` | Số dư tiền hiện tại (đơn vị: nghìn đồng, hiển thị `Xk`). |
| `earned` | `int` | `sim` | Tổng doanh thu kiếm được trong lượt. |
| `reputation` | `float` | `sim` | Điểm uy tín của quán (miền `[0.0, 5.0]`, mặc định `3.0`, hiển thị số sao & thanh uy tín). |
| `score` | `int` | `runner.Session` | Điểm tổng hợp: `earned + 100 * floor(reputation)`. |
| `meta` | `object` | `LiveGame` | Bản sao `tuning[mode]` từ `game.contract.json` (`bounds`, `dock_pos`, `dock_radius`, `interact_radius`, `catch_radius`, `patience_s`, `eat_s`, `tip_min_patience_ratio`, v.v.) để UI vẽ đúng bán kính mà không hard-code. |
| `events` | `array` | `LiveGame` | Tối đa 40 sự kiện gần nhất `[{type:"event", tick, phase, name, data}]` để hiển thị nhật ký sự kiện trực tiếp và kích hoạt hiệu ứng/âm thanh. |
| `finished` | `bool` | `LiveGame` | `true` khi ca chơi đã kết thúc (`session.done`). |
| `reason` | `string \| null` | `LiveGame` | Lý do kết thúc ca (`"time"`, `"docked"`, `"fainted"`, `"error"`, hoặc `null` khi đang chơi). |
| `error` | `string \| null` | `LiveGame` | Traceback nếu code `sim` ném ngoại lệ (hiển thị cảnh báo đỏ trên màn hình). |

---

### 2.2. Trường riêng của buổi sáng (`mode == "gather"`)

| Đường dẫn trường | Kiểu | Ý nghĩa & hiển thị trên HUD `gather` |
|---|---|---|
| `player.pos` | `[float, float]` | Tọa độ `[x, d]` của Út Sen (mét). `x` ngang $[0, 100]$, `d` sâu $[0, 30]$. |
| `player.vel` | `[float, float]` | Vận tốc hiện tại `[vx, vd]` (m/s) sau khi chặn biên. |
| `player.heading_deg` | `float` | Góc hướng mặt ($0^\circ = +x$, $90^\circ = +d$ xuống dưới). |
| `player.at_surface` | `bool` | `true` nếu $d \le \text{surface\_depth}$ ($0.5\text{ m}$). Hiển thị huy hiệu **"Mặt nước (Hái/Bến - E)"** hoặc **"Dưới nước (Bắt cá - Space)"**. |
| `player.oxygen_ticks` | `int` | Lượng oxy còn lại (tick). Chia 60 để hiển thị giây trên thanh Oxy. |
| `player.oxygen_max_ticks` | `int` | Oxy tối đa (`oxygen_max_s * 60` = 1800 tick = 30s). Khi tỷ lệ $< 25\%$ thanh Oxy chuyển màu đỏ cảnh báo. |
| `player.zero_oxy_ticks` | `int` | Bộ đếm ngạt khi `oxygen_ticks == 0` và ở dưới nước ($[0, 59]$). Đủ 60 tick thì mất 1 Máu (`choke`). HUD hiển thị thanh cảnh báo ngạt khi $> 0$. |
| `player.hp` | `int` | Máu hiện tại của Út Sen ($[0, \text{hp\_max}]$). Hiển thị bằng biểu tượng trái tim `♥` / `♡`. |
| `player.hp_max` | `int` | Máu tối đa (`3`). |
| `player.catch_cd_ticks` | `int` | Thời gian hồi chiêu bắt cá còn lại (tick). Khi $> 0$, hiển thị thanh đếm ngược hồi chiêu. |
| `player.invuln_ticks` | `int` | Số tick nhấp nháy bất tử tạm thời (nếu có). |
| `hold` | `string[]` | Danh sách nguyên liệu trong giỏ theo **thứ tự nhặt (LIFO — phần tử cuối là mới nhất)**. |
| `hold_count` | `int` | Số ô đã dùng trong giỏ (`len(hold)`). |
| `hold_capacity` | `int` | Sức chứa tối đa của giỏ (`12` ô). Vẽ từng ô giỏ, đánh dấu ô mới nhất (`LIFO`) và thống kê số lượng từng loại. |
| `nodes[]` | `array` | Danh sách điểm hái trên mặt nước: `{id, pos: [x, d], kind, ready, regrow_ticks}`. Khi `ready == false`, hiển thị vòng/số giây mọc lại `ceil(regrow_ticks / 60)`. |
| `fish[]` | `array` | Danh sách đàn cá dưới nước: `{id, pos: [x, d], kind, heading_deg}`. Vẽ đàn cá theo loài (`ca_linh`, `ca_loc`) kèm nhãn `id` và sản lượng (`yield`). |

---

### 2.3. Trường riêng của buổi tối (`mode == "quan"` — Quán nhỏ nhà bè)

| Đường dẫn trường | Kiểu | Ý nghĩa & hiển thị trên HUD `quan` |
|---|---|---|
| `player.pos` | `[float, float]` | Tọa độ `[x, z]` của Út Sen trên nhà bè ($x \in [0, 16]$, $z \in [0, 10]$ hướng bắc). |
| `stock` | `{[kind]: int}` | **Tồn kho vật lý** hiện tại trên nhà bè (bao gồm cả nguyên liệu đang bị đơn `reserved` giữ chỗ). |
| *(Tính trên UI)* **Kho khả dụng** | `{[kind]: int}` | Tính bằng `stock[kind] - sum(c.reserved[kind] cho mọi c trong customers)`. Hiển thị rõ `Khả dụng / Tổng tồn (Đang giữ)` để người chơi biết quán còn đủ nguyên liệu đón khách mới hay không. |
| `hand` | `object \| null` | Món Út Sen đang bưng trên tay: `{"order_id": str, "dish_id": str, "base_price": int}` hoặc `null` khi tay trống. Hiển thị cả trên đầu nhân vật lẫn thẻ HUD **"Trên tay"**. |
| `stoves[]` | `array` | Danh sách bếp (`B1`): `{id, pos: [x, z], state, dish, cook_ticks_left, ready_ticks}`.<br>- `state == "idle"`: Rỗi (nhấn `E` để nấu đơn `reserved` cũ nhất).<br>- `state == "cooking"`: Đang nấu `dish.dish_id` cho `dish.order_id`, hiển thị thanh tiến độ & số giây còn lại `ceil(cook_ticks_left / 60)`.<br>- `state == "ready"`: Món đã chín, chờ Út Sen nhấn `E` để bưng (`ready_ticks` đếm tuổi món). |
| `tables[]` | `array` | Danh sách bàn (`T1`): `{id, pos: [x, z], customer_id}` (`null` nếu bàn trống). |
| `customers[]` | `array` | Danh sách khách đang ngồi tại bàn: `{id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status, reserved, base_price, tip}`.<br>- `state`: `"waiting"` (đang đợi món) hoặc `"eating"` (đang ăn).<br>- `order_status`: `"reserved"` (đợi nấu) \| `"assigned"` (đang nấu/trên tay) \| `"served"` (đã phục vụ) \| `"unfulfillable"` (không thể phục vụ).<br>- `patience_ticks_left`: Thanh kiên nhẫn còn lại, có vạch mốc **50% (`tip_min_patience_ratio`)** báo hiệu ngưỡng nhận tiền boa (`+20%` giá món & `+0.2` uy tín).<br>- `eat_ticks_left`: Thanh thời gian khách ăn còn lại trước khi trả tiền (`paid`). |

---

## 3. Cơ chế nạp Tài nguyên Đồ họa & Âm thanh mở rộng (`chonoi/web/assets/`)

Để nhóm có thể bổ sung hình nền, spritesheet và nhạc nền bất cứ lúc nào mà không ảnh hưởng tới logic hay headless:
- Máy chủ `chonoi/live.py` phục vụ các file tĩnh trong thư mục `chonoi/web/assets/` qua đường dẫn HTTP `/assets/<tên-file>`.
- Nếu file tài nguyên chưa có trong `chonoi/web/assets/`, client `chonoi/web/index.html` tự động dùng bộ vẽ Canvas 2D miền Tây Nam Bộ mặc định (không báo lỗi, không chặn vòng lặp render).
