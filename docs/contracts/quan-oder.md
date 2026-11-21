# Hợp đồng tích hợp P1-03 (Customer) ↔ P1-04 (Kitchen)

Nguồn: PRD-0 Phase 1, Test Contract v1.0, các mục A, D, E, F, G. Đây là bản trích rút để hai thành viên chốt interface; không thay thế PRD gốc.

## 1. Cấu trúc data theo PRD

- `quan.stock`: map `kind -> số lượng vật lý` (bao gồm cả số đang được giữ chỗ). `available = stock[kind] - tổng reserved của các đơn còn reserved`.
- `quan.customers[]`: `id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip` (một số field có thể được mặc định/điền khi chuyển trạng thái theo contract và code).
- `state` khách: `waiting`, `eating` theo các trạng thái được mô tả tại PRD.
- `order_status`: `reserved`, `assigned`, `unfulfillable`, `served`.
- `reserved`: map `kind -> số lượng`, phải bằng đúng công thức ở đơn `reserved`; khi `assigned` thì phần giữ rỗng và một món tương ứng nằm ở bếp hoặc tay.
- `quan.stoves[]`: `id`, `pos`, `state` (`idle`/`cooking`/`ready`), `dish`, `cook_ticks_left`, `ready_ticks`.
- `quan.hand`: `null` hoặc payload `{ "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60 }`.
- `quan.tables[]`: `id`, `pos`; khi snapshot có thêm `customer_id` (suy ra từ khách đang ngồi).

**Quy ước trách nhiệm cần xác nhận trong nhóm:** P1-03 quản lý sinh khách, chọn món, reservation, patience và customer_left. P1-04 quản lý bếp, assigned, served, eating, paid, tiền/uy tín do thanh toán và đóng ca; phối hợp rõ hàm xử lý khi khách rời/đóng ca để tránh xử lý đôi.

## 2. Công thức cố định trong game.contract.json

| Dish ID | Recipe | cook_s | price (nghìn đồng) |
|---|---|---:|---:|
| `ca_loc_nuong_trui` | `ca_loc: 1` | 6 | 60 |
| `goi_bong_sung` | `bong_sung: 2` | 4 | 40 |
| `lau_ca_linh_dien_dien` | `ca_linh: 3`, `bong_dien_dien: 1` | 10 | 120 |

Không hardcode thay cho đọc tuning; ví dụ là preset PRD.

## 3. Fixture mẫu để dev P1-04 độc lập

`tests/fixtures/p1_04_reserved_order.json`:

```json
{
  "quan": {
    "random_customers": false,
    "stock": {"ca_loc": 1},
    "player": {"pos": [2, 8]},
    "customers": [
      {
        "id": "C1",
        "table_id": "T1",
        "dish_id": "ca_loc_nuong_trui",
        "order_tick": 0,
        "state": "waiting",
        "patience_ticks_left": 3600,
        "order_status": "reserved",
        "reserved": {"ca_loc": 1}
      }
    ]
  }
}
```

Đây là **fixture đề xuất** dựa trên schema PRD, **chưa phải fixture đã xác nhận chạy thành công trong repo**. Codex phải kiểm tra validator/loader hiện tại, bổ sung default trường đúng spec nếu cần, và chạy test trước khi xác nhận hợp lệ. Nếu dùng scenario `stock`, không truyền thêm `--inventory` cùng lúc.

## 4. Quy tắc xử lý mỗi tick (F, Quán)

1. Tăng phase_tick, giảm ca, nấu, ăn và kiên nhẫn.
2. Bếp xong thì ready (chỉ tăng ready_ticks nếu đã ready đầu bước).
3. Di chuyển rồi xử lý **tối đa một** tương tác ở cạnh lên, chọn theo `(khoảng cách, bếp trước bàn, ID)`; không fallback khi đối tượng gần nhất không tương tác được.
4. Bếp idle chọn đơn reserved cũ nhất `(order_tick, table_id)`, tiêu nguyên liệu và chuyển assigned. Bếp ready chuyển món lên tay trống. Bàn nhận đúng order_id, khách eating, tip tính ngay tại phục vụ.
5. Khách ăn xong paid rồi rời. Khách hết kiên nhẫn rời nếu ca còn thời gian. Đóng ca: đang ăn phải thanh toán `closing`, đang chờ rời `closing` không trừ uy tín; phát quan_end.
6. Chỉ nếu ca còn thời gian: đến lịch thì sinh khách mới.

Không khẳng định chốt hẳn *ownership* các hàm Python cho tới khi hai người cùng xác nhận. Hai bên nên tránh sửa trùng vùng `quan.py`; ưu tiên helper riêng và API nhỏ.

## 5. Điều kiện bàn giao

- Có test dùng scenario để kiểm tra cook_started → dish_ready → dish_picked → served → paid; event/snapshot và các tick đúng PRD.
- Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` trên code tích hợp.
- Không sửa `game.contract.json` ngoài thay team/team_size do nhóm quyết định; không đổi names/shape output JSONL.
- Ghi rõ dependency/assumption và yêu cầu người 3 review bản này trước khi merge.
