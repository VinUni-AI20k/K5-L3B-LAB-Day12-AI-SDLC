# Spec & Acceptance Criteria — Phase 2 · M4 (`day`, `Shop`, `Pause`)

- **Phụ trách:** Nguyễn Nhật Minh (`NhMinh-2610` — M4)
- **Tài liệu chuẩn:** `Ticket02.md` (mục 2, 4.1–4.5), `phase-2-task.md`
- **Phạm vi:** Test Contract v1.1 — không ảnh hưởng Test Contract v1.0 khi chạy ở Phase 1.

---

## 1. Giao diện móc nối giữa M4 với M1/M2/M3/M5/M6

- **`runner.py` (`Session` — Pause ở cả 3 mode `gather`, `quan`, `day`):**
  - Quản lý `self.paused: bool = False`, `self.tick` (bước ngoài) và `self.sim_tick` (bước gameplay).
  - Mỗi bước `step(inp)`:
    1. Xét cạnh lên `inp.pressed("pause")` **trước tiên**:
       - Nếu đang không pause → đặt `self.paused = True`, chỉ tăng `self.tick += 1`, **không** tăng `sim_tick`/`phase_tick`/timer, bỏ qua mọi hành động & `buy`, phát `paused` (`{}`).
       - Nếu đang pause → đặt `self.paused = False`, phát `resumed` (`{}`), và **chạy tiếp gameplay ngay trong bước đó** (tăng `sim_tick`, `phase_tick`, xử lý hành động bình thường).
    2. Nếu vẫn đang pause (không có cạnh `pause`) → chỉ tăng `self.tick += 1`, bỏ qua mọi cạnh hành động & `buy`, không phát event.
  - `snapshot()` khi `self.paused == True` xuất `"state": "paused"`.
- **`chonoi/sim/shop.py` (Shop độc lập, dùng trong `DaySim`):**
  - Đọc bảng nâng cấp từ `tuning["shop"]`: `max_ticks` (600), `upgrades.oxygen[]`, `upgrades.hp[]`.
  - Nhận `money`, `upgrades` (map cấp đã mua), `stock` (kho dư từ ca tối).
  - Xử lý **1 lệnh `buy` trước cạnh `shop_done`** kể cả ở bước cuối cùng (`time_left_ticks` về 0).
  - Đóng bằng `shop_done` → `shop_end({"reason": "done"})`; tự hết 600 tick → `shop_end({"reason": "time"})`.
- **`chonoi/sim/day.py` (`DaySim` — chế độ `--mode day --days 1..5`):**
  - Nhận `tuning`, `scenario`, `streams`, `ids`, `days` (1..5, mặc định 1).
  - Giữ trạng thái xuyên Ngày: `day` (1..N), `days_completed`, `money`, `earned`, `reputation`, `upgrades` (đã mua), `active_upgrades` (đang áp dụng cho Ngày hiện tại), `day_plan` (ghi đè từ `scenario.day.day_plan` nếu có).
  - Truyền `active_upgrades` vào `GatherSim` (`oxygen_max_s`, `hp_max` theo cấp) và truyền danh sách món trong `day_plan["dishes"]` vào `QuanSim` (phối hợp với M3 `M3.3`) cùng kho bàn giao trong bộ nhớ (`gather_end.inventory["items"]`).
  - **Không dùng** `quan.stock` hay `quan.reputation` trong `day`; khi mở quán, kiểm tra tính hợp lệ của `scenario.quan` (khách/bếp/món theo `day_plan`) trên kho thực lúc mở quán — mâu thuẫn → `BadInput` (mã thoát `2`).
  - Vỏ event trong `day` luôn có thêm `"day": self.day`. Snapshot mọi pha trong `day` luôn có thêm `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase` (`"gather"|"quan"|"shop"`), `phase_tick`. Dòng `end` thêm `days_completed` và `reason: "days_complete"` khi hoàn thành đủ `--days`.

---

## 2. Danh sách Acceptance Criteria (`AC-P2-M4-01` → `AC-P2-M4-09`)

| Mã AC | Phạm vi | Điều kiện đạt (Acceptance Criteria) |
|---|---|---|
| `AC-P2-M4-01` | Pause (3 mode) | Cạnh lên `pause` ở `gather`/`quan`/`day`: bước vào pause chỉ tăng `tick`, giữ nguyên `sim_tick`/`phase_tick`/timer, phát `paused`, snapshot `state:"paused"`, bỏ qua `move`/`interact`/`catch`/`buy`/`shop_done`. |
| `AC-P2-M4-02` | Resume ngay bước | Cạnh lên `pause` lần 2 phát `resumed` và thực thi ngay gameplay + hành động của bước đó (tăng `sim_tick`, `phase_tick`). Giữ nút qua bước không tạo cạnh mới. |
| `AC-P2-M4-03` | Pause trong Shop | Pause trong Shop đóng băng `time_left_ticks` (600 tick) và bỏ qua `buy`/`shop_done`; resume xong mới đếm tiếp. |
| `AC-P2-M4-04` | Shop mua `oxygen`/`hp` | Mua đúng cấp kế tiếp (`oxygen`: 200→45s, 400→60s; `hp`: 250→4, 500→5). Đủ đúng giá vẫn mua được. Trừ `money`, giữ nguyên `earned` và `score`. Cập nhật `upgrades` ngay, phát `bought {upgrade,level,price,money}`. |
| `AC-P2-M4-05` | Shop lỗi `buy_failed` | Thiếu tiền → `buy_failed(reason:"funds")`; đã max cấp → `buy_failed(reason:"max_level")`; lệnh lạ/mở rộng chưa bật → `buy_failed(reason:"unknown")`. Tiền và cấp giữ nguyên. |
| `AC-P2-M4-06` | Shop đóng & thứ tự cuối bước | `buy` xử lý trước `shop_done` kể cả ở tick cuối (`time_left_ticks` về 0). Có `shop_done` phát `shop_end(reason:"done")`; hết 600 tick không nhấn nút phát `shop_end(reason:"time")`. |
| `AC-P2-M4-07` | Đổi pha cùng tick trong `day` | Tick 0 dựng Ngày 1: `day_start` → `day_plan` → `phase_start(gather)`. Sau `gather_end` (kể cả `fainted` với kho rỗng) dựng quán & phát `phase_start(quan)` cùng tick. Sau `quan_end` dựng Shop & phát `phase_start(shop)` cùng tick. Snapshot đổi pha có `phase_tick: 0`, pha mới chạy từ bước sau. |
| `AC-P2-M4-08` | Chuyển Ngày & `active_upgrades` | Đóng Shop tăng `days_completed`. Nếu chưa đủ `--days`, dựng Ngày kế ngay tick đó: sao `upgrades → active_upgrades`, hồi đầy oxy/Máu theo `active_upgrades` mới, làm mới giỏ, bỏ kho dư, giữ `money`/`earned`/`reputation`. Đủ `--days` → `end` có `reason:"days_complete"`, `days_completed == days`. |
| `AC-P2-M4-09` | Hiệu năng & Tất định `day` | `--mode day --days 1` (≤ 22.200 tick) chạy nhanh hơn 20 s; cùng seed + input cho JSONL giống nhau từng byte. |

---

## 3. Lưu ý phối hợp cho M5 (UI) & M6 (Contract/Scenario)

- **M5 (`thanhvu101`):** UI Shop đọc `snapshot.upgrades`, `snapshot.active_upgrades`, `snapshot.money`, `snapshot.stock`, `snapshot.time_left_ticks` và gửi `buy` (`"oxygen"` / `"hp"`) hoặc `shop_done: true`; Pause đọc `snapshot.state == "paused"` và gửi `pause: true`.
- **M6 (`K0heii`):** `scenario.py` v1.1 kiểm `0 <= money <= earned`, cấm `quan.stock`/`quan.reputation` khi `--mode day`, tính lại `day_plan.ingredients` nếu khai.
