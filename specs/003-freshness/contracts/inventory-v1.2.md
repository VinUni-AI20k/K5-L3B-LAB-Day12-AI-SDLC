# Kho cá thể v1.2 (đề xuất cho `docs/contracts/` — TV1 chốt)

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```
- Đúng một khóa gốc `items`; giá trị là mảng (rỗng `[]` hợp lệ).
- Mỗi phần tử đúng 3 khóa `id` (chuỗi khác rỗng, duy nhất), `kind` (danh mục 6 nguyên liệu), `fresh` (số hữu hạn ∈ [0,100], không bool).
- `contract_version` = "1.2": kho đếm (`items` là object) hoặc bất kỳ vi phạm nào → mã 2 trước khi ghi đầu ra.
- Ghi: một lần khi `gather_end`; file tạm cùng thư mục + thay thế nguyên tử; sắp theo id (GIẢ ĐỊNH: so sánh theo số của `I<n>`, như `ids.sort_by_id`); `fresh` đủ chính xác (không round 3).
- Ngất → `{"items":[]}`; `tick_limit` → không đụng đích.
- `gather_end.data.inventory` cùng schema.
- Kho quán nhận mọi cá thể kể cả ươn; sức chứa chỉ áp cho giỏ.
