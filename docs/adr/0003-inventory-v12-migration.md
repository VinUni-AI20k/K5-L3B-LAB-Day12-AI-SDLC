# ADR-0003: Phân tích tác động & Chuyển đổi Schema Kho Cá thể (Contract v1.2 — Phase 3)

## 1. Bối cảnh (TICKET-03 — Mùa Nước Nổi)
Khách hàng yêu cầu theo dõi độ tươi (`fresh` $\in [0, 100]$) của từng cá thể nguyên liệu từ lúc Út Sen bắt/hái ở Gather cho tới lúc đưa vào bếp ở Quán. Schema kho đếm theo loại (`{"items": {"ca_linh": 3}}`) ở v1.0–v1.1 được **thay thế hoàn toàn** bằng kho cá thể:
```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

## 2. Bảng phân tích tác động & Phân công nhóm (5 thành viên)

| Module | File cần đổi | Test bị ảnh hưởng (giữ / đổi / thêm) | Người phụ trách |
|---|---|---|---|
| **Manifest & Schema Adapter** | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/scenario.py` | Đổi test schema kho trong `test_smoke_p1.py`; thêm `test_gather_phase3_tv1.py` (từ chối kho đếm $\to$ mã 2) | **TV1 (`htphong23`)** |
| **Lặn (Hao tươi, LIFO, Dòng lũ `current`)** | `chonoi/sim/gather.py` | Đổi fixture `hold` trong `test_gather_lat1.py`, `test_gather_monsters.py`; thêm test ngưỡng `spoiled` tại 30 & `current` trong `test_gather_phase3_tv1.py` | **TV1 (`htphong23`)** |
| **Lặn (Cấp ID `I1..In` khi hái/bắt cá)** | `chonoi/sim/gather.py` (`_try_gather`, `_try_catch`) | Đổi `test_gather_actions.py`, `test_gather_fish.py` sang kiểm mảng cá thể `{id, kind, fresh: 100}` | **TV2 (`thangdktd`)** |
| **Quán (Hao tươi kho, giữ chỗ theo ID, thử giữ lại khi ươn)** | `chonoi/sim/quan.py` (`stock`, `_load_customers`, `reserved`) | Đổi `test_quan_customers.py`, `test_quan_day_menu.py` sang `stock` cá thể & `reserved` mảng ID; thêm test re-reserve / `unfulfillable` | **TV3 (`daohiep2903`)** |
| **Quán & Day (Chốt `base_price` theo độ tươi, bàn giao `day`)** | `chonoi/sim/quan.py` (`cook_started`, `_tip`), `chonoi/sim/day.py` | Đổi `test_day_mode.py`, `test_quan_leftovers.py`; thêm test `base_price = floor(price * avg_fresh / 100)` và tăng ID `I` xuyên Ngày | **TV4 (`NTLam108`)** |
| **HUD, QA & Verification** | `chonoi/web/index.html`, `docs/verification/phase-3.md`, `docs/proof/phase-3/` | Giữ `test_live.py`, `test_team_check.py`; chạy smoke bàn giao kho v1.2 & regression P1–P2 | **TV5 (`vuhieuvh`)** |

## 3. Quyết định kỹ thuật & Độ chính xác ở ngưỡng 30
1. **Biểu diễn chính xác độ tươi bằng `Fraction` (lưới 240 đơn vị/điểm tươi):**
   - Tốc độ hao tươi ở Gather là $0.5/\text{s} = 1/120 = 2/240$ mỗi tick; ở Quán là $0.25/\text{s} = 1/240$ mỗi tick.
   - `chonoi/inventory.py` cung cấp `to_fraction(val)` và `fresh_to_num(val)`: mọi giá trị trên lưới $u / 240$ ($u \in [0, 24000]$) khi xuất ra JSONL (làm tròn 3 chữ số thập phân) và đọc lại đều ánh xạ song ánh 1–1 chính xác tuyệt đối về lại $u / 240$, bảo toàn tuyệt đối nhánh so sánh ở ngưỡng `spoiled_below = 30` và phép `math.floor` khi chốt `base_price`.
2. **Thứ tự tích hợp để giữ `main` ổn định:**
   - **Bước 1 (TV1):** Đẩy nhánh `feat/p3-tv1-schema-gather` gồm `game.contract.json` (v1.2), adapter `chonoi/inventory.py`, `chonoi/scenario.py`, và logic độ tươi + dòng nước lũ `current` trong `chonoi/sim/gather.py`.
   - **Bước 2 (TV2, TV3, TV4 song song):** TV2 cập nhật test hái/bắt cá; TV3 & TV4 cập nhật `chonoi/sim/quan.py` và `chonoi/sim/day.py` theo đúng adapter `inventory.py` của TV1.
   - **Bước 3 (Phút 20 — Smoke & Merge):** Ghép Gather + Quán + Day, chạy smoke bàn giao kho cá thể qua file và trong `day`, cập nhật HUD & bằng chứng verification của TV5 trước khi gắn tag `phase-3`.
