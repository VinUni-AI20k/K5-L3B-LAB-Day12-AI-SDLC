# ĐẶC TẢ KỸ THUẬT CHI TIẾT: DEV 2 — HỆ SINH THÁI & SĂN BẮT CÁ SÔNG MEKONG

> **Dự án:** Quán Ăn Chợ Nổi (Day 12 — AI SDLC)  
> **Người thực hiện:** Phạm Quang Tuấn (2A202603824) — `phamtuan2xx3-alt`  
> **Module phụ trách:** `chonoi/sim/gather.py`  
> **Phạm vi:** Cơ chế Hái Bông Điên Điển, Bông Súng; Săn Bắt Cá Linh, Cá Lóc; Hồi chiêu; Quản lý Giỏ đồ LIFO & Sức chứa.

---

## 1. TỔNG QUAN HỆ THỐNG & TRIẾT LÝ THIẾT KẾ (DAVE THE DIVER MEKONG)
Lấy cảm hứng từ vòng lặp cốt lõi của **Dave the Diver**, cơ chế của DEV 2 chịu trách nhiệm tạo ra nguồn nguyên liệu tươi sống cho nhà hàng đêm thông qua hai hoạt động:
1. **Hái nông sản trên mặt nước ($d \le \text{surface\_depth} = 0.5$):** Nhặt Bông Điên Điển, Bông Súng.
2. **Săn thủy sản dưới lòng sông ($d > 0.5$):** Bắt Cá Linh (theo đàn), Cá Lóc (đơn độc, lặn sâu).
3. **Cơ chế túi đồ (Inventory Hold Capacity):** Giới hạn tối đa 12 món. Buộc người chơi phải tính toán sức chứa cho công thức món ăn của nhà hàng tối.

---

## 2. THÔNG SỐ TUNING & CẤU TRÚC DỮ LIỆU CỐT LÕI

Mọi thông số kỹ thuật được nạp trực tiếp từ `game.contract.json["tuning"]["gather"]`:

| Tham số | Giá trị | Đơn vị | Ý nghĩa nghiệp vụ |
| :--- | :---: | :---: | :--- |
| `surface_depth` | `0.5` | mét | Ranh giới giữa Mặt Nước và Lòng Sông |
| `interact_radius` | `2.0` | mét | Bán kính tối đa để hái hoa trên mặt nước |
| `node_yield` | `1` | món | Sản lượng mỗi lần hái 1 bụi hoa |
| `regrow_s` | `20.0` | giây | Thời gian mọc lại của hoa ($20 \times 60 = 1200$ ticks) |
| `catch_radius` | `2.0` | mét | Bán kính quăng lưới/vợt bắt cá |
| `catch_cooldown_s` | `0.5` | giây | Thời gian hồi chiêu bắt cá ($0.5 \times 60 = 30$ ticks) |
| `fish_yield.ca_linh` | `3` | con | Bắt 1 đàn Cá Linh nhận 3 con vào giỏ |
| `fish_yield.ca_loc` | `1` | con | Bắt 1 con Cá Lóc nhận 1 con vào giỏ |
| `hold_capacity` | `12` | món | Dung tích tối đa của giỏ đồ |

### Cấu trúc thực thể trong Bộ nhớ:
```python
# Nút hoa (Nodes)
{
    "id": "N1",                    # ID duy nhất (N1..N4)
    "kind": "bong_dien_dien",      # "bong_dien_dien" | "bong_sung"
    "pos": [12.0, 0.0],            # [x, d] (d luôn = 0.0)
    "regrow_ticks": 0              # 0: sẵn sàng (ready), > 0: đang mọc lại
}

# Đàn cá (Fish)
{
    "id": "F1",                    # ID duy nhất (F1..F6)
    "kind": "ca_linh",             # "ca_linh" | "ca_loc"
    "pos": [15.0, 5.0],            # [x, d] (d > 0.5)
    "heading_deg": 0.0             # Hướng bơi
}

# Giỏ đồ (Hold Bag - LIFO)
self.hold = ["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"]  # Cuối mảng là mới nhất
self.catch_cd_ticks = 0            # Bộ đếm hồi chiêu bắt cá (ticks)
```

---

## 3. ĐẶC TẢ NGHIỆP VỤ & THUẬT TOÁN CHI TIẾT

### 3.1. Thuật toán Hái Hoa Mặt Nước (`inp.pressed("interact")`)
- **Điều kiện kích hoạt:**
  1. Phím `interact` có cạnh lên (`pressed("interact") == True`).
  2. Nhân vật **không** nằm trong bến thuyền (`not self._in_dock()`).
  3. Nhân vật đang ở mặt nước: `self._at_surface()` (tức $d \le 0.5$).
- **Quy trình thực thi:**
  1. Lọc danh sách ứng viên từ `self.nodes`:
     $$\text{candidates} = \{ n \in \text{self.nodes} \mid n[\text{regrow\_ticks}] == 0 \land \text{dist}(\text{self.pos}, n[\text{pos}]) \le 2.0 \}$$
  2. **Luật Tie-breaking (Giải quyết hòa cự ly):**
     Sắp xếp danh sách ứng viên theo khóa: `(dist(self.pos, n["pos"]), n["id"])`. Chọn phần tử đầu tiên.
  3. **Kiểm tra Sức chứa Giỏ đồ:**
     - Nếu $\text{len}(\text{self.hold}) \ge 12$:
       * Bắn sự kiện: `("hold_full", {})`
       * Không tăng số lượng đồ trong giỏ.
       * Node hoa giữ nguyên trạng thái sẵn sàng (không tính là đã hái).
     - Nếu $\text{len}(\text{self.hold}) < 12$:
       * Thêm `self.t["node_yield"]` (1) phần tử `n["kind"]` vào cuối mảng `self.hold`.
       * Đặt lại thời gian mọc: $n[\text{regrow\_ticks}] = \text{round}(20.0 \times 60) = 1200$.
       * Bắn sự kiện: `("gather", {"node_id": n["id"], "kind": n["kind"]})`.

### 3.2. Thuật toán Hoa Mọc Lại (Regrowth Cycle)
- Thực hiện ở đầu mỗi tick (bước 1 của `step()`):
  - Duyệt `self.nodes` (theo thứ tự `sort_by_id`):
  - Nếu $n[\text{regrow\_ticks}] > 0$:
    * $n[\text{regrow\_ticks}] \leftarrow n[\text{regrow\_ticks}] - 1$
    * Nếu $n[\text{regrow\_ticks}] == 0$: bắn sự kiện `("node_regrown", {"node_id": n["id"]})`.

### 3.3. Thuật toán Săn Bắt Cá Dưới Sông (`inp.pressed("catch")`)
- **Điều kiện kích hoạt:**
  1. Phím `catch` có cạnh lên (`pressed("catch") == True`).
  2. Nhân vật đang ở **dưới nước**: `not self._at_surface()` (tức $d > 0.5$).
  3. Đã hết hồi chiêu: `self.catch_cd_ticks == 0`.
- **Quy trình thực thi:**
  1. **Kích hoạt Hồi chiêu ngay lập tức:**
     $$\text{self.catch\_cd\_ticks} = \text{round}(0.5 \times 60) = 30 \text{ ticks}$$
  2. Lọc danh sách cá trong tầm:
     $$\text{candidates} = \{ f \in \text{self.fish} \mid \text{dist}(\text{self.pos}, f[\text{pos}]) \le 2.0 \}$$
  3. Nếu $\text{candidates}$ rỗng: Quăng lưới hụt, kết thúc thao tác (chỉ mất hồi chiêu).
  4. Nếu có cá trong tầm:
     * **Luật Tie-breaking:** Sắp xếp theo `(dist(self.pos, f["pos"]), f["id"])`. Chọn cá $f$ gần nhất.
     * **Kiểm tra Sức chứa Giỏ đồ:**
       - Nếu $\text{len}(\text{self.hold}) \ge 12$:
         * Bắn sự kiện: `("hold_full", {})`.
         * Cá **không** bị bắt, vẫn bơi nguyên vẹn trong `self.fish`.
       - Nếu $\text{len}(\text{self.hold}) < 12$:
         * Lấy sản lượng: $Y = \text{self.t}["\text{fish\_yield}"][f["\text{kind}"]]$ (Cá Linh: 3, Cá Lóc: 1).
         * Số lượng có thể nạp: $\text{add\_count} = \min(Y, 12 - \text{len}(\text{self.hold}))$.
         * Thêm `add_count` phần tử $f[\text{kind}]$ vào cuối `self.hold`.
         * **Xóa cá khỏi thực thể sống:** Loại bỏ cá $f$ khỏi mảng `self.fish`.
         * Bắn sự kiện: `("fish_caught", {"fish_id": f["id"], "kind": f["kind"]})`.

---

## 4. MA TRẬN 10 CA BIÊN HIỂM HÓC (EDGE CASES MATRIX)

| Mã Case | Tình huống giả định | Hành vi chuẩn xác theo Test Contract | Rủi ro nếu code ẩu |
| :---: | :--- | :--- | :--- |
| **EC-01** | Bấm `interact` khi đang ở trong dock | DEV 1 xử lý `docked`, DEV 2 KHÔNG được hái dù có node gần | Bị hái lén lúc cập bến, sai lý do kết thúc game |
| **EC-02** | Bấm `interact` hái hoa khi $d = 0.5001$ | Bị từ chối vì $d > 0.5$ (không ở mặt nước) | Hái hoa dưới lòng sông làm mất tính chân thực |
| **EC-03** | Bấm `catch` khi $d = 0.5$ (mặt nước) | Bị từ chối vì đang ở mặt nước (chỉ bắt được khi $d > 0.5$) | Không tốn hồi chiêu, không bắt cá |
| **EC-04** | Giỏ còn 1 chỗ trống ($11/12$), bắt Cá Linh ($Y=3$) | Thêm 1 Cá Linh vào giỏ (đạt $12/12$), cá F vẫn bị bắt và xóa khỏi sông | Giỏ bị tràn quá 12 hoặc crash mảng |
| **EC-05** | Giỏ đã đầy $12/12$, bấm Space gần cá | Bắn sự kiện `hold_full`, cá KHÔNG bị xóa khỏi sông | Cá biến mất oan uổng mà giỏ không nhận được |
| **EC-06** | Hai con cá F1, F2 cách người chơi bằng nhau | Bắt con cá có ID nhỏ hơn theo chuỗi ký tự (`F1 < F2`) | Không tất định byte-for-byte giữa 2 lần chạy |
| **EC-07** | Bấm Space liên tục trong 30 tick hồi chiêu | Chỉ tick đầu tiên xử lý, 29 tick sau bị bỏ qua hoàn toàn | Spam bắt sạch cá trong 1 khung hình |
| **EC-08** | Node hoa bị hái ở tick $T$ | Đúng tick $T + 1200$, node phát sự kiện `node_regrown` | Mọc sớm hoặc trễ 1 tick làm lệch Test Contract |
| **EC-09** | Kịch bản scenario cấp danh sách cá rỗng | Quăng lưới không crash `IndexError`, hồi chiêu vẫn đếm | Crash game runtime khi scenario test cá rỗng |
| **EC-10** | Giỏ đồ xuất kho ở cuối ca lặn | Thứ tự xuất kho `hold_to_items` tổng hợp đúng số lượng | Thiếu nguyên liệu cho ca mở quán buổi tối |

---

## 5. THIẾT KẾ MODULE ĐỘC LẬP CHUẨN XÁC (ĐÃ ĐƯỢC SWARM PHÊ DUYỆT)

Tất cả logic của DEV 2 được phân tách thành 2 phương thức chuyên biệt trong `chonoi/sim/gather.py`:
1. `_step_harvest(self, events)`: Đặt tại Bước 3 (sau kiểm tra dock).
2. `_step_catch(self, events)`: Đặt tại Bước 4.

```python
from ..ids import id_key, sort_by_id

    # --- BƯỚC 3: HÁI NÚT HOA MẶT NƯỚC (DEV 2) ---
    def _step_harvest(self, events):
        """Hái hoa tại mặt nước (d <= surface_depth), tie-breaking id_key tự nhiên."""
        if not self._at_surface():
            return
        cands = [n for n in self.nodes if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
        if not cands:
            return
        cands.sort(key=lambda n: (round(math.dist(self.pos, n["pos"]), 6), id_key(n["id"])))
        chosen = cands[0]
        capacity = self.t["hold_capacity"]
        if len(self.hold) >= capacity:
            events.append(("hold_full", {}))
            return
        yield_n = self.t.get("node_yield", 1)
        space = capacity - len(self.hold)
        add_n = min(yield_n, space)
        self.hold.extend([chosen["kind"]] * add_n)
        chosen["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": chosen["id"], "kind": chosen["kind"]}))

    # --- BƯỚC 4: SĂN BẮT CÁ LÒNG SÔNG (DEV 2) ---
    def _step_catch(self, events):
        """Bắt cá dưới nước (d > surface_depth), cooldown 30 ticks, tie-breaking id_key."""
        if self._at_surface() or self.catch_cd_ticks > 0:
            return
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        cands = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
        if not cands:
            return  # Quăng hụt: vẫn mất hồi chiêu 30 ticks
        cands.sort(key=lambda f: (round(math.dist(self.pos, f["pos"]), 6), id_key(f["id"])))
        chosen = cands[0]
        capacity = self.t["hold_capacity"]
        if len(self.hold) >= capacity:
            events.append(("hold_full", {}))
            return
        y = self.t["fish_yield"].get(chosen["kind"], 1)
        space = capacity - len(self.hold)
        add_n = min(y, space)
        self.hold.extend([chosen["kind"]] * add_n)
        self.fish = [f for f in self.fish if f["id"] != chosen["id"]]
        events.append(("fish_caught", {"fish_id": chosen["id"], "kind": chosen["kind"]}))
```

---

## 6. DANH SÁCH BỘ TEST ĐỘC LẬP (`tests/test_dev2_harvest_catch.py`)

1. `test_harvest_flower_success`: Bơi đến N1, bấm E $\rightarrow$ nhận `bong_dien_dien`.
2. `test_harvest_underwater_blocked`: Lặn sâu $d=1.0$, bấm E $\rightarrow$ không nhặt được.
3. `test_harvest_hold_full`: Giỏ 12 món, bấm E $\rightarrow$ phát `hold_full`, hoa vẫn còn.
4. `test_catch_ca_linh_yield_3`: Lặn gần F1, bấm Space $\rightarrow$ nhận 3 con Cá Linh, F1 biến mất.
5. `test_catch_ca_loc_yield_1`: Lặn gần F2, bấm Space $\rightarrow$ nhận 1 con Cá Lóc, F2 biến mất.
6. `test_catch_cooldown_active`: Bấm Space 2 lần liên tiếp $\rightarrow$ chỉ bắt được 1 lần.
7. `test_catch_at_surface_blocked`: Đang ở mặt nước bấm Space $\rightarrow$ không bắt được cá.
8. `test_catch_hold_near_full_cap`: Giỏ 11 món, bắt Cá Linh $\rightarrow$ chỉ nhận 1 con (đủ 12), cá F1 vẫn bị xóa.
9. `test_flower_regrowth_after_20s`: Đếm đúng 1200 ticks $\rightarrow$ phát sự kiện `node_regrown`.
10. `test_tie_breaking_order`: 2 thực thể cách đều người chơi $\rightarrow$ ưu tiên bắt ID nhỏ hơn.
