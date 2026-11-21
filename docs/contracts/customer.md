# Hợp đồng: schema một khách (Quán)

> Lát 3 chốt; lát 4 và QA dùng.
> Bản dưới là **khung gợi ý** — lát 3 chốt lại theo PRD-0 rồi báo nhóm. Đổi sau khi chốt thì ghi lý do ở cuối file.

## Trường (trong `sim.customers` và snapshot `customers[]`)

| Trường | Kiểu | Ý nghĩa | Ai ghi |
|---|---|---|---|
| `id` | str | Cấp bằng `sim.ids` (IdAllocator) | lát 3 |
| `table_id` | str | Bàn khách ngồi | lát 3 |
| `dish` | str | Món đã chọn (khóa trong `menu`) | lát 3 |
| `state` | str | Xem bảng trạng thái | lát 3, lát 4 |
| `patience_ticks` | int | Kiên nhẫn còn lại (chờ món) | lát 3 |
| `eat_ticks` | int | Thời gian ăn còn lại | lát 4 |
| `reserved` | object | Nguyên liệu đã giữ chỗ `{kind: n}` | lát 3 |
| … | | (bổ sung theo PRD-0) | |

## Trạng thái và chuyển trạng thái

| `state` | Từ đâu | Sang đâu | Sự kiện |
|---|---|---|---|
| `waiting` | khách mới (lát 3) | `eating` (phục vụ, lát 4) / rời đi (lát 3) | `customer_arrived`?, `customer_left` |
| `eating` | `served` (lát 4) | rời đi sau khi trả tiền (lát 4) | `served`, `paid` |
| … | | | |

## Quy tắc chung
- Danh sách khách luôn sắp bằng `ids.sort_by_id`.
- Giữ chỗ: nguyên liệu trong `reserved` **không** được dùng cho khách khác; khách bỏ đi thì trả lại kho.

## Lịch sử thay đổi
- (chưa có)
