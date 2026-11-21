# Changelog
## Unreleased

### Phase 3 — Bếp & Độ tươi (Contract v1.2, `chonoi/sim/kitchen.py`)
- **Breaking / Schema mới (v1.2):**
  - `sim.stock` hỗ trợ mảng cá thể `[{"id": "I1", "kind": "...", "fresh": 100}, ...]` và `customers[].reserved` là mảng `id` cá thể (vẫn giữ tương thích ngược khi `sim.stock` là `dict` đếm theo loại ở v1.0/v1.1).
  - `cook_started.data.items` xuất mảng cá thể sắp theo `(kind, id_key)` và chốt `base_price = floor(giá niêm yết × trung bình fresh / 100)` (nhân thêm `1.5` rồi `floor` nếu là đơn đặt trước `reservation_id`).
  - Khi cháy món (`burn_s`), bỏ qua cá thể ươn (`fresh < spoiled_below`), giữ lại cá thể tươi nhất (hòa theo `id_key`), hoặc chuyển `failed` nếu là đơn đặt trước.
