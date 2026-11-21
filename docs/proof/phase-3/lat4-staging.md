# Lát 4 – chuẩn bị tích hợp Phase 3 (chưa nghiệm thu)

- **Người phụ trách:** `nguyenhung1901`.

## Phần đã chuẩn bị

| AC theo kế hoạch P3 | Logic trong Lát 4 | Giới hạn kiểm chứng |
|---|---|---|
| P3-11 | `_tick_freshness` gọi `chonoi.items.decay` (0.25/s, cả hàng giữ) và phát `spoiled` theo id; snapshot là mảng cá thể | Đã thử với adapter giả, chưa có `chonoi/items.py` của Lát 0 |
| P3-14 | `cook_started` tiêu đúng các id giữ, mang cá thể trong `items`, `base_price = floor(price × avg_fresh/100)` | Đã thử trực tiếp `_interact`, chưa có scenario v1.2 end-to-end |
| P3-15 | Boa dùng `base_price` đã chốt; Burn thử giữ lại toàn công thức từ hàng chưa ươn, không trùng id giữa hai bếp | Đã thử bằng adapter giả, chưa có test QA `test_fresh_p3.py` |
| P3-17 | Khung Quán giữ dữ liệu list/snapshot v1.2; không chấp nhận chứng nhận scenario mới | **Chưa xong** `_validate_quan` của Lát 4; cần merge schema chung từ Lát 0/Lát 3 trước |

## Các phụ thuộc bắt buộc trước khi merge Phase 3

1. **Lát 0:** `chonoi/items.py` với `decay`, `is_spoiled`, `pick_freshest`; `inventory.py`, `contract.py`, `scenario.py` nhận schema cá thể + `tuning.freshness`.
2. **Lát 3:** `_init_customers`, `_available`, `_reserve`, `_release` chuyển `reserved` từ map đếm sang mảng id; `_retry_spoiled(events)` được gọi sau `_tick_freshness` và trước nấu. Code Lát 4 không tự sửa các hàm đó.
3. **Lát 4:** Sau khi nền v1.2 merge, hoàn thiện `_validate_quan` cho `hand`, `stoves`, giá động và stock id (phải tránh xung đột với lát 0).
4. **QA/PO:** Merge `test_fresh_p3.py`, chép toàn văn Ticket-03, xác nhận thứ tự event và kiểu trả về `pick_freshest`, chạy `QA_STRICT=1` cùng smoke v1.2.

## Kiểm thử có thể lặp lại

```powershell
$env:PYTHONPATH = 'tests;.'
$env:CHONOI_HEADLESS_CMD = 'python -m chonoi.headless'
python -m unittest discover -s tests -p 'test_quan_lat4.py' -v
```

**Kết quả tại thời điểm xây bản vá:** 30 test Lát 4 PASS (24 test hiện có + 6 test chuẩn bị Phase 3), không SKIP. Trong 6 test Phase 3, nếu chưa có `chonoi.items`, helper dùng adapter giả theo chữ ký kế hoạch; **chưa chứng minh tích hợp thật**. Hồi quy toàn bộ repository cần chạy lại trên máy thành viên ở commit áp dụng bản vá.

**Trạng thái:** bản chuẩn bị, không đánh dấu các AC P3 đạt cho đến khi tích hợp đủ các lát.
