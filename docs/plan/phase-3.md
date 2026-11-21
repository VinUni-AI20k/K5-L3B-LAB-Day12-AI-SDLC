# Kế hoạch Phase 3 (1:55 – 2:30 · Test Contract v1.2 — "Mùa Nước Nổi")

## 1. Phân tích tác động (Breaking Change: Kho đếm → Kho cá thể)

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| **Adapter & Contract** | `game.contract.json` (`freshness`, bật `1.2` ở `M6.4`), `chonoi/freshness.py` *(mới)*, `chonoi/inventory.py`, `chonoi/scenario.py`, `chonoi/headless.py` | Thêm `tests/test_freshness_v12_m6.py`; giữ 145 test v1.1 xanh trong lúc dev, chuyển fixture kho cũ sang v1.2 khi bật `1.2` | **Nguyễn Như Duy An (M6)** |
| **Lặn — Độ tươi & Rơi hàng** | `chonoi/sim/gather.py`, `chonoi/sim/monsters.py` | Cập nhật `test_gather_m1.py`, `test_gather_m1_p2.py`; thêm test `spoiled` ngưỡng `fresh=30`, `lost` cá thể LIFO | **Vũ Quang Huy (M1)** |
| **Lặn — Giỏ cá thể & Kho** | `chonoi/sim/gather.py` | Cập nhật `test_gather_m2.py`, `test_gather_m2_p2.py`; thêm test cấp id `I1, I2…` xuyên ngày & xuất kho cá thể | **Nguyễn Minh Quang (M2)** |
| **Quán — Kho tươi & Giữ chỗ** | `chonoi/sim/quan_customers.py`, `chonoi/sim/quan.py` | Cập nhật `test_quan_customers_m3.py`, `test_quan_m3_v11.py`; thêm test giữ theo `id` tươi nhất, nhả & giữ lại khi ươn → `unfulfillable` | **Phùng Văn Thanh Cao (M3)** |
| **Quán — Giá tươi & Vòng ngày** | `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py` | Cập nhật `test_quan_m4.py`, `test_day_shop_pause_m4.py`; thêm test `base_price` theo `avg_fresh`, `cook_started.items` cá thể, bàn giao kho cá thể trong `day` | **Nguyễn Nhật Minh (M4)** |
| **HUD Độ tươi** | `chonoi/web/index.html` *(đã có adapter đọc v1.2)* | `test_live_m5.py` + chụp ảnh bằng chứng HUD hiển thị độ tươi & hàng ươn | **Vũ Quang Thanh (M5)** |

## 2. Quyết định kỹ thuật & Thứ tự tích hợp (giữ `main` luôn chạy được)
1. **Biểu diễn chính xác tránh sai số float ở ngưỡng `30` và phép `floor` giá**: Mọi module M1–M4 dùng chung helper [`chonoi/freshness.py`](../../chonoi/freshness.py) với `FRESH_SCALE = 240` (`-2` đơn vị/tick ở `gather`, `-1` đơn vị/tick ở `quan`; `calc_fresh_base_price` chia nguyên chính xác).
2. **Chuyển đổi không làm vỡ `main` giữa chừng**:
   - Đợt 1 (`M6.1`–`M6.3`): thêm khối `freshness` vào `game.contract.json`, thêm `chonoi/freshness.py`, hỗ trợ song song `v1.1` / `v1.2` trong `inventory.py` & `scenario.py` theo `contract_version` (giữ `contract_version: "1.1"` trên `main` để 145+ test đang chạy vẫn xanh 100%).
   - Đợt 2–3: M1–M4 chuyển `gather`, `quan`, `day`, `shop` sang kho cá thể và dùng `chonoi/freshness.py`.
   - Đợt 4 (`M6.4`): Khi M1–M4 đã merge xong, M6 đổi 1 dòng `"contract_version": "1.2"` trong `game.contract.json` → lập tức bật chế độ từ chối file kho đếm bằng mã `2`, chạy smoke 2 tiến trình + `day` + regression, ghi breaking change vào `CHANGELOG.md`, chốt `docs/verification/phase-3.md` và gắn tag `phase-3` trước **2:30**.
