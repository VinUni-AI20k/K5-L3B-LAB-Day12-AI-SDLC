# ADR 0003: Chuyển schema kho sang danh sách cá thể và độ tươi `v1.2`

- **Trạng thái:** Chấp nhận (Phase 3 — TICKET-03)
- **Bối cảnh:** Ở `v1.0/v1.1`, file kho và `quan.stock` dùng map đếm `{kind: count}` còn `gather.hold` là mảng `kind`. Yêu cầu mới "Mùa Nước Nổi" đòi hỏi theo dõi độ tươi từng cá thể (`I1, I2, ...`) xuyên suốt `gather -> quan -> shop -> Ngày kế`, phân biệt hàng ươn (`fresh < 30`) và tính giá món theo độ tươi trung bình.
- **Quyết định:**
  1. **Schema mới:** `items` là mảng object `{"id": str, "kind": str, "fresh": number}` (sắp theo `id_key` khi xuất kho / `quan.stock`; `gather.hold` giữ thứ tự nhặt LIFO). File kho đếm kiểu cũ trả `BadInput` (mã thoát `2`) ở `v1.2`.
  2. **Số học cố định chống sai số float:** Dùng đơn vị nguyên `FRESH_SCALE = 240` (`100` điểm = `24000` đơn vị, ngưỡng `30` = `7200` đơn vị). Gather hao `-2` đơn vị/tick (`0.5/s`); Quán hao `-1` đơn vị/tick (`0.25/s`). Khi chuyển đổi JSON giữ chính xác biểu diễn so với ngưỡng `30` (tránh làm tròn `29.999` lên `30`).
  3. **Trình tự tích hợp giữ `main` luôn xanh:**
     - **Turn 4 (`Besoi2004`):** Chốt ADR/Impact Matrix -> nâng contract `v1.2` + `inventory.py` + `scenario.py` -> hoàn thiện Gather độ tươi/`spoiled`/LIFO + adapter tương thích trong `quan.py`/`day.py` + cập nhật toàn bộ test hồi quy.
     - **Turn 5 (`letuandat131`):** Hoàn thiện Quán `v1.2` (hao `-1`/tick, tái giữ chỗ một lần khi ươn/`unfulfillable`, `base_price` theo độ tươi trung bình), mở rộng `burn` (`burn_s = 20`, `dish_burnt`), cập nhật UI độ tươi & cháy món, `CHANGELOG.md` và tag `phase-3`.
- **Hệ quả:** Schema cũ bị từ chối rõ ràng với mã `2`; mọi module và test phụ thuộc được cập nhật đồng bộ ngay trong lượt chuyển đổi.
