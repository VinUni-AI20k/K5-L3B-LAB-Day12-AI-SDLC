# Changelog

## [1.2.0] - Phase 3: Change Request "Mùa Nước Nổi"

### Breaking Changes
- **Schema kho nguyên liệu (Inventory Schema)**:
  - Chuyển đổi từ kho đếm số lượng (`{"items": {"ca_loc": 1}}`) sang kho cá thể (`{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`).
  - File kho v1.2 phải có đúng khóa `items` là mảng cá thể. File kho đếm kiểu cũ bị từ chối với mã thoát 2.
- **Giỏ đồ (`gather.hold`)**:
  - Mỗi nguyên liệu trong giỏ là một cá thể độc lập có `id` (I1, I2, ...), `kind` và `fresh` (0..100).
- **Mất hàng (LIFO)**:
  - Khi ngất hoặc rơi hàng, danh sách `lost` trả về mảng cá thể theo thứ tự nhặt sau bỏ trước.

### Added
- **Độ tươi (Freshness) trong Lặn & Hái (`gather`)**:
  - Hàng mới hái / bắt cá có `fresh = 100.0`, cấp ID liên tục xuyên ca/ngày (`I1, I2, ...`).
  - Hao tươi giỏ đồ với tốc độ 0.5/s (kẹp đáy ở 0.0), bắt đầu hao từ bước sau khi nhặt.
  - Sự kiện `spoiled`: phát đúng 1 lần khi cá thể vượt ngưỡng từ $\ge 30$ xuống $< 30$.
- **Cấu hình `freshness`**:
  - Thêm cấu hình trong contract v1.2: `freshness: {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.
- **Bàn giao kho cá thể**:
  - Cập bến xuất file kho cá thể với độ tươi thực tế sau các bước lặn.
  - Ngất (`fainted`) ghi file kho rỗng `{"items": []}`.
- **Quán và đơn đặt trước**:
  - Kho cá thể trong Quán hao tươi 0.25/s; cá thể dưới 30 bị loại và phát `spoiled`.
  - Đơn giữ nguyên liệu bằng ID cá thể, chốt giá theo độ tươi; Phase 3 thêm hai đơn đặt trước có giữ bàn, kiểm kho, thời hạn và uy tín.
  - Snapshot/event Quán và HUD hiển thị cá thể, độ tươi và trạng thái đơn đặt trước.
