# Spec & Acceptance Criteria — Phase 3 · M4 (giá theo độ tươi, kho cá thể trong `day`/Shop)

- **Phụ trách:** Nguyễn Nhật Minh (`NhMinh-2610` — M4)
- **Tài liệu chuẩn:** `Ticket03.md` (Test Contract v1.2 "Mùa Nước Nổi"), `phase-3-task.md`
- **Ràng buộc:** Chỉ bật khi `contract_version: "1.2"`. Trước đó giữ adapter để test P1–P2 không gãy (M6 bật v1.2 ở `M6.4`).

---

## 1. Kho cá thể (schema v1.2)

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

- `id` duy nhất, `kind` thuộc danh mục nguyên liệu, `fresh` hữu hạn trong `[0,100]`.
- Kho quán nhận nguyên số lượng, `id`, độ tươi kể cả hàng ươn. Trần giỏ chỉ áp lên giỏ, không áp lên kho quán.
- Trong `day`: bàn giao trong **cùng tick** chuyển pha, hàng **không hao thêm** lúc bàn giao; ca quán chạy từ bước sau.
- Shop **không hao tươi**; hàng thô ở Shop hoặc chờ nhập không đổi `fresh`.
- Id cá thể tiếp tục tăng xuyên pha và Ngày (`I1, I2, …`), kể cả khi cá thể trước đã dùng hoặc bỏ.

## 2. Biểu diễn số chính xác (điểm dễ nghẽn #1)

Dùng chung toàn nhóm: `fresh_units = round(fresh × 240)` (số nguyên).

| Nơi | Hao mỗi tick | Tương ứng |
|---|---|---|
| Giỏ (gather) | 2 đơn vị | 0.5 điểm/s |
| Kho quán | 1 đơn vị | 0.25 điểm/s |

- So ngưỡng ươn: `fresh_units < 30 × 240 = 7200` (so **trước** khi làm tròn).
- Giá chốt: `base_price = floor(giá_niêm_yết × avg_fresh / 100)` tính bằng số nguyên:
  `base_price = (giá × tổng_units) // (100 × 240 × n)` với `n` = số cá thể dùng. Không dùng float.
- Xuất JSONL: `fresh = units / 240`, làm tròn tối đa 3 chữ số (dung sai quan sát ±0.01).

## 3. Phần việc của M4 (không đụng phần hao tươi/giữ chỗ của M1–M3)

| Hạng mục | Mô tả |
|---|---|
| Tiêu đúng id đang giữ | Khi bếp idle lấy đơn `reserved` cũ nhất, tiêu **đúng các id** trong `reserved` (mảng id), loại khỏi kho. |
| Chốt giá theo tươi | `base_price` chốt lúc `cook_started`, theo công thức mục 2, lưu vào payload món/bếp/tay. |
| Boa | `tip = floor(base_price × tip_rate)` trên **giá đã chốt**, giữ điều kiện kiên nhẫn ≥ 50%. |
| `cook_started.items` | Mảng cá thể `{id, kind, fresh}` sắp theo `(kind, id)` (dùng `id_key`). |
| Bàn giao `day` | `gather_end.inventory` (mảng cá thể) → `quan` cùng tick → kho dư sang Shop (không hao) → Ngày kế bỏ kho dư theo luật hiện hành. |

## 4. Danh sách AC (`AC-P3-M4-01` → `AC-P3-M4-07`)

| Mã AC | Điều kiện đạt |
|---|---|
| `AC-P3-M4-01` | Nấu `ca_loc_nuong_trui` với 1 cá thể `fresh=100` → `base_price = 60`. |
| `AC-P3-M4-02` | Nấu `lau_ca_linh_dien_dien` (3 cá linh + 1 điên điển) với `fresh` lần lượt `100, 90, 80, 70` → `avg=85`, `base_price = floor(120×85/100) = 102`. |
| `AC-P3-M4-03` | Giá luôn `floor`, không làm tròn lên: `avg_fresh=97.5`, giá 60 → `58` (không phải 59). |
| `AC-P3-M4-04` | Boa tính trên giá đã chốt: giá chốt 102, đủ điều kiện → `tip = floor(102×0.2) = 20` (không phải 24). |
| `AC-P3-M4-05` | `cook_started.data.items` là mảng cá thể sắp `(kind, id)`; `I10` đứng sau `I2` cùng kind. |
| `AC-P3-M4-06` | Cá thể đã dùng nấu bị loại khỏi kho quán; id không bị cấp lại ở Ngày sau. |
| `AC-P3-M4-07` | `day`: kho cá thể `{id, kind, fresh}` đi nguyên vẹn gather→quan trong cùng tick; Shop không làm đổi `fresh`; snapshot Shop có `stock` dạng mảng cá thể. |

## 5. Phụ thuộc & điểm nối

- **M2 (Quang):** cấp id `I1, I2…`, xuất `gather_end.inventory` mảng cá thể.
- **M3 (Cao):** hao tươi kho thô, `spoiled`, giữ chỗ theo id tươi nhất (`reserved` là mảng id). M4 chỉ **đọc** `reserved` đã giữ xong.
- **M6 (An):** `inventory.py`/`scenario.py` v1.2, bật `contract_version: "1.2"`.
- **M5 (Thanh):** HUD đọc `hold`/`stock` mảng cá thể.
