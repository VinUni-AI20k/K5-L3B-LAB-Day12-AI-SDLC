# Changelog

Định dạng theo Keep a Changelog, ghi theo Test Contract.

## Unreleased

### Breaking changes (Test Contract v1.2, Ticket-03 "Mùa Nước Nổi")

> Trạng thái khi viết: nền v1.2 (`chonoi/fresh.py`, đọc/ghi hai schema, PR #20) đã vào `main`, nhưng manifest vẫn là `1.1` cho tới khi các lát giỏ, giữ chỗ, kho quán gộp xong. Bảng dưới là hợp đồng v1.2 sẽ có hiệu lực khi bật `contract_version: "1.2"`.

Kho đếm `{"items": {"ca_loc": 1}}` đổi thành **kho cá thể** `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`. Khi manifest bật `contract_version: "1.2"`:

| Chỗ | Trước (v1.0 / v1.1) | Sau (v1.2) |
|---|---|---|
| File kho (`--inventory`, `--inventory-out`) | `{"items": {"kind": số}}` | `{"items": [{"id", "kind", "fresh"}]}`, sắp theo id. Kho đếm ở v1.2 trả mã thoát **2** |
| `scenario.gather.hold` | `["ca_loc", "bong_sung"]` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]` |
| `scenario.quan.stock` | `{"ca_loc": 2}` | `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]` |
| `customers[].reserved` (scenario và snapshot) | `{"ca_loc": 1}` | mảng **id** cá thể, ví dụ `["I1", "I4"]` |
| Snapshot `hold`, `stock` | chuỗi kind / số đếm | mảng cá thể `{id, kind, fresh}` |
| `cook_started.data.items` | mảng kind | mảng cá thể, sắp theo kind rồi id |
| `monster_hit.data.lost`, `faint.data.lost` | mảng kind | mảng cá thể theo thứ tự bỏ LIFO |
| Giá món | `base_price` = giá niêm yết | `floor(giá niêm yết × TB fresh / 100)` lúc bắt đầu nấu; boa tính trên giá đã chốt |

### Thêm mới
- Độ tươi: `freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`; tính bằng 240 đơn vị/điểm. Hàng `fresh < 30` là **ươn**: chiếm ô, không nấu được.
- Event `spoiled{item_id, kind, location}` (`location`: `hold` hoặc `stock`), phát đúng một lần khi đi từ ≥ 30 xuống < 30.
- Đơn không đủ nguyên liệu tươi chuyển `unfulfillable`.
- HUD: thanh độ tươi trên từng ô giỏ, nhãn "ƯƠN", dòng "Độ tươi kho" ở quán, kho khả dụng chỉ tính hàng chưa ươn và chưa giữ. `?demo=fresh` (chỉ để QA xem HUD, mặc định tắt).
- Skill `smoke-day`, `smoke-p3`; test `tests/test_p3_hud_qa.py`.

### Cách cập nhật fixture và file kho
1. Đặt `contract_version` đúng bản đang chạy. Với v1.2, thêm khối `freshness` (bắt buộc, cấm ở v1.1).
2. `gather.hold`: đổi từng chuỗi kind thành `{"id": "I<n>", "kind": "<kind>", "fresh": 100}`, id duy nhất, tăng dần theo thứ tự vào giỏ.
3. `quan.stock`: đổi `{"kind": n}` thành `n` cá thể cùng kind với id duy nhất giữa `hold` và `stock`.
4. `customers[].reserved`: đổi thành mảng id trỏ tới cá thể chưa ươn có trong `stock`, đủ công thức, không dùng chung giữa các đơn.
5. File kho cũ (`{"items": {...}}`) phải chạy lại gather ở v1.2 để sinh file mới, hoặc đổi tay theo bảng trên.
6. Id cá thể cấp theo thứ tự vào giỏ, **tăng xuyên pha và xuyên Ngày** (một `IdAllocator` cho cả lượt).

### Lịch sử trước đó
- Phase 2 (v1.1): 6 nguyên liệu, 6 món, `pause`, `--mode day`, Cá Sấu + Rắn Hổ Mây (`snake`), 2 bếp 4 bàn.
- Phase 1 (v1.0): lát gather, quan, HUD pixel art, smoke 2 tiến trình.
