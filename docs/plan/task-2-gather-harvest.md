# DEV 2: GAMEPLAY SĂN BẮT & SINH THÁI SÔNG (`sim/gather`)

> **File code phụ trách:** `chonoi/sim/gather.py`  
> **Nhiệm vụ:** Xây dựng cơ chế hái Bông Điên Điển, Bông Súng trên mặt nước, săn bắt Cá Linh, Cá Lóc dưới sông và quản lý giỏ đồ LIFO.

---

## 1. YÊU CẦU TÍNH NĂNG GAME CẦN CODE
1. **Quản lý Giỏ đồ (Hold Capacity & LIFO):**
   - Giỏ đồ `self.hold` chứa danh sách tên nguyên liệu theo thứ tự nhặt (cuối mảng là mới nhất).
   - Dung tích tối đa: `self.t["hold_capacity"]`.
   - Khi cố nhặt hoặc bắt mà giỏ đã đầy (`len(self.hold) >= self.t["hold_capacity"]`): phát sự kiện `hold_full`, `data: {}`, không thêm đồ vào giỏ.
2. **Cơ chế Hái Bông trên Mặt nước:**
   - Khi nhấn `interact` (ở ngoài dock) và nhân vật đang ở mặt nước (`self._at_surface()`):
     + Quét các node bông có `regrow_ticks == 0` trong bán kính `self.t["interact_radius"]`.
     + Chọn node gần nhất (nếu bằng khoảng cách, chọn node có `id` nhỏ hơn theo `sort_by_id`).
     + Nếu tìm thấy: kiểm tra giỏ. Nếu giỏ đầy $\rightarrow$ phát `hold_full`. Nếu còn chỗ $\rightarrow$ thêm `self.t["node_yield"]` item `node["kind"]` vào `self.hold`, gán `node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))`, phát sự kiện `gather`, `data: {"node_id": node["id"], "kind": node["kind"]}`.
3. **Cơ chế Săn bắt Cá dưới sông:**
   - Khi nhấn `catch`: chỉ hợp lệ khi đang dưới nước (`not self._at_surface()`) và đã hết hồi chiêu (`self.catch_cd_ticks == 0`).
   - Đặt lại thời gian hồi chiêu: `self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))`.
   - Quét tìm con cá gần nhất trong bán kính `self.t["catch_radius"]` (nếu bằng khoảng cách, chọn id nhỏ hơn).
   - Nếu tìm thấy cá: kiểm tra giỏ. Nếu giỏ đầy $\rightarrow$ phát `hold_full`.
   - Nếu còn chỗ: số lượng nhận được theo `yield_count = self.t["fish_yield"][fish["kind"]]`. Thêm tối đa `min(yield_count, space_left)` vào `self.hold`. Xóa cá đó khỏi mảng `self.fish`. Phát sự kiện `fish_caught`, `data: {"fish_id": fish["id"], "kind": fish["kind"]}`.

---

## 2. LỆNH CHẠY TEST THỬ NGHIỆM
```bash
# Windows
$env:PYTHONPATH="tests;."; py -3 -m unittest tests.test_smoke_p1.Contract.test_gather_snapshot_has_gather_fields -v

# Linux / Mac
PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1.Contract.test_gather_snapshot_has_gather_fields -v
```

---

## 3. PROMPT COPY-PASTE CHO AI AGENT
```text
Bạn là lập trình viên gameplay phụ trách phát triển cơ chế "Săn Bắt & Sinh Thái Sông" trong file `chonoi/sim/gather.py`.

Hãy triển khai logic tương tác Hái Bông và Bắt Cá trong phương thức `step(inp)` của class `GatherSim`:
1. Hái nút ở mặt nước:
   - Trong khối `if inp.pressed("interact")`: nếu không ở trong dock và đang ở mặt nước (`self._at_surface()`):
     * Tìm tất cả các node trong `self.nodes` thỏa mãn: `n["regrow_ticks"] == 0` và `math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]`.
     * Nếu có, sắp xếp theo `(math.dist(self.pos, n["pos"]), n["id"])` và chọn node đầu tiên.
     * Kiểm tra giỏ: nếu `len(self.hold) >= self.t["hold_capacity"]`: phát event ("hold_full", {}).
     * Nếu còn chỗ: nhặt `self.t["node_yield"]` item `n["kind"]` vào `self.hold`, đặt `n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))`, phát event ("gather", {"node_id": n["id"], "kind": n["kind"]}).
2. Bắt đàn cá:
   - Trong khối `if inp.pressed("catch")`:
     * Chỉ xử lý nếu `not self._at_surface()` và `self.catch_cd_ticks == 0`.
     * Đặt `self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))`.
     * Tìm cá trong `self.fish` có `math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]`.
     * Sắp xếp theo `(math.dist(self.pos, f["pos"]), f["id"])` và chọn cá gần nhất.
     * Nếu có cá: nếu `len(self.hold) >= self.t["hold_capacity"]`: phát event ("hold_full", {}).
     * Nếu giỏ còn chỗ: số lượng thêm = `self.t["fish_yield"].get(f["kind"], 1)`. Thêm số lượng đó vào `self.hold` (tối đa không vượt quá hold_capacity). Xóa cá khỏi `self.fish`. Phát event ("fish_caught", {"fish_id": f["id"], "kind": f["kind"]}).
Đảm bảo code chạy tương thích với toàn bộ các trường trong snapshot. Chạy test sau khi code xong.
```
