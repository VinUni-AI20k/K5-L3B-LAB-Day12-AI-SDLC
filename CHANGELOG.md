# CHANGELOG

## [Contract v1.2 — Phase 3: Mùa Nước Nổi] — 2026-11-21

### ⚠️ Breaking Changes (Thay đổi không tương thích ngược so với v1.0 / v1.1)
1. **Schema File Kho (`--inventory-out` / `--inventory`) & `gather_end.data.inventory`:**
   - **Trước (v1.0–v1.1):** Kho đếm theo loại `{"items": {"ca_linh": 3, "ca_loc": 1}}`, kho rỗng `{"items": {}}`.
   - **Mới (v1.2):** Kho cá thể `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 97.5}]}`, kho rỗng `{"items": []}`.
   - File kho đếm hoặc sai schema / `id` trùng / `kind` lạ / `fresh` ngoài `[0, 100]` bị từ chối với mã thoát `2` (`BadInput`).
2. **Schema Scenario & Snapshot (`gather.hold`, `quan.stock`, `customers[].reserved`):**
   - `gather.hold`: Từ mảng chuỗi mã nguyên liệu `["ca_loc", "bong_sung"]` chuyển sang mảng cá thể `[{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]`.
   - `quan.stock`: Từ object đếm `{"bong_sung": 2}` chuyển sang mảng cá thể `[{"id": "I1", "kind": "bong_sung", "fresh": 100}, ...]`.
   - `customers[].reserved`: Từ object đếm `{"bong_sung": 2}` chuyển sang mảng ID cá thể `["I1", "I2"]`.
3. **Payload sự kiện `monster_hit`, `faint`, `cook_started`:**
   - `lost` trong `monster_hit` và `faint`: Mảng các cá thể `{id, kind, fresh}` theo thứ tự bỏ LIFO.
   - `cook_started.data.items`: Mảng các cá thể `{id, kind, fresh}` tiêu dùng cho món ăn, sắp theo `kind` rồi `id`.

### Hướng dẫn cập nhật Fixture & Test cũ
- Thay mọi `"hold": ["ca_loc", "bong_sung"]` trong fixture gather bằng:
  ```json
  "hold": [
    {"id": "I1", "kind": "ca_loc", "fresh": 100},
    {"id": "I2", "kind": "bong_sung", "fresh": 100}
  ]
  ```
- Thay mọi `"stock": {"bong_sung": 2}` trong fixture quán bằng:
  ```json
  "stock": [
    {"id": "I1", "kind": "bong_sung", "fresh": 100},
    {"id": "I2", "kind": "bong_sung", "fresh": 100}
  ]
  ```
- Thay kiểm tra kho rỗng `{"items": {}}` bằng `{"items": []}`.

### Tính năng mới (Phase 3)
- **Độ tươi (`freshness`):** Khởi tạo `fresh = 100`, hao `0.5/s` ở giỏ Gather và `0.25/s` ở kho Quán. Phát sự kiện `spoiled` (`{item_id, kind, location}`) đúng một lần theo thứ tự `id` khi độ tươi đi từ $\ge 30$ xuống $< 30$.
- **Giữ chỗ theo ID & Chốt giá theo độ tươi (`base_price`):** Chọn cá thể khả dụng chưa ươn tươi nhất (hòa theo `id`); tự động nhả và thử giữ lại 1 lần khi cá thể đang giữ bị ươn; chốt `base_price = floor(listed_price * avg_fresh / 100)`.
- **Mở rộng — Dòng nước lũ (`current`):** Khai báo `"extensions": ["current"]` và `tuning.gather.current`. Phát `current_warning` ở $t - 120$, `current_start` ở $t = 1800k$ kéo dài $480$ tick, đẩy người chơi $\pm 1.5\text{ m/s}$ khi $d_{\text{đầu bước}} \ge 10$, phát `current_end(elapsed|phase_end)`.
