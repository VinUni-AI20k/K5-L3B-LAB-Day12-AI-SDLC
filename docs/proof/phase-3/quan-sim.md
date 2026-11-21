# Bằng chứng triển khai Module sim/quan (Phase 3 - Test Contract v1.2)

**Người thực hiện:** Nguyễn Văn Lâm (`sim/quan` · Integrator)  
**Nhánh:** `lam`  
**Phạm vi:** 
- [game.contract.json](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/game.contract.json)
- [chonoi/contract.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/contract.py)
- [chonoi/inventory.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/inventory.py)
- [chonoi/scenario.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/scenario.py)
- [chonoi/sim/quan.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/sim/quan.py)
- [tests/test_quan.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/tests/test_quan.py)
- [docs/contracts/inventory.v12.sample.json](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/docs/contracts/inventory.v12.sample.json)

---

## 1. Các hạng mục đã hoàn thành theo TICKET-03 (Phase 3)

1. **Hợp đồng & Cấu hình v1.2:**
   - Đặt `contract_version: "1.2"`.
   - Bổ sung cấu hình `freshness` vào `tuning`: `initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`.
   - Kiểm tra `freshness` hợp lệ trong `chonoi/contract.py`.

2. **File kho cá thể & Schema Contract v1.2 (`chonoi/inventory.py`):**
   - Hỗ trợ mảng cá thể `[{"id": "I1", "kind": "ca_linh", "fresh": 100.0}, ...]`.
   - Kiểm tra id chuỗi duy nhất khác rỗng, kind thuộc danh mục, fresh trong `[0, 100]`.
   - Contract v1.2 từ chối file kho đếm (`{"items": {"ca_loc": 1}}`), trả `BadInput` (mã thoát 2) theo đúng tiêu chí DoD.
   - Ghi kho nguyên tử qua file tạm cùng thư mục, sắp xếp theo ID cá thể.

3. **Cập nhật Scenario v1.2 (`chonoi/scenario.py`):**
   - Hỗ trợ `quan.stock` là mảng cá thể.
   - Hỗ trợ `customers[].reserved` là mảng ID cá thể trỏ vào kho khả dụng chưa ươn, khớp công thức món, không dùng chung đơn khác.
   - Kiểm tra mâu thuẫn và trường lạ trả mã 2.

4. **Luật chơi Quán Phase 3 (`QuanSim` trong `chonoi/sim/quan.py`):**
   - **Thang đo chính xác:** Dùng 240 đơn vị mỗi điểm tươi (`SCALE = 240`), hao 1 đơn vị/tick ở quán (0.25/s), đảm bảo tất định và chính xác tuyệt đối ở ngưỡng 30.
   - **Ươn & sự kiện `spoiled`:** Khi `fresh < 30`, phát event `spoiled` đúng một lần theo ID cá thể (`location: "stock"`). Hàng ươn vẫn chiếm ô kho nhưng không dùng nấu.
   - **Giữ chỗ theo cá thể tươi nhất:** Lấy các cá thể khả dụng có `fresh >= 30` có độ tươi cao nhất, hòa theo ID nhỏ.
   - **Tái giữ chỗ khi hàng ươn:** Khi cá thể trong đơn `reserved` bị ươn, nhả toàn bộ phần giữ và thử giữ lại đúng một lần (xử lý theo `order_tick` rồi ID bàn). Nếu không đủ hàng tươi thì chuyển sang `unfulfillable`.
   - **Chốt giá theo độ tươi:** Khi `cook_started`, tiêu đúng các ID cá thể đang giữ và chốt `base_price = floor(giá niêm yết * avg_fresh / 100)`. Mảng `items` trong `cook_started` sắp theo `kind` rồi `id`.
   - **Tính boa & phục vụ:** Khách kiên nhẫn $\ge 50\%$ lúc giao được tính boa `floor(base_price * 0.2)` trên giá đã chốt theo độ tươi. Nhận boa dương cộng $+0.2$ uy tín.

---

## 2. Kết quả kiểm thử

### Lệnh chạy:
```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest tests.test_quan -v
```

### Kết quả:
```text
test_freshness_decay_and_spoiled_event (tests.test_quan.TestQuanPhase3Freshness.test_freshness_decay_and_spoiled_event) ... ok
test_multiple_spoiled_emitted_in_id_order (tests.test_quan.TestQuanPhase3Freshness.test_multiple_spoiled_emitted_in_id_order) ... ok
test_reservation_by_freshest_items (tests.test_quan.TestQuanPhase3Freshness.test_reservation_by_freshest_items) ... ok
test_reserved_item_spoils_and_no_stock_becomes_unfulfillable (tests.test_quan.TestQuanPhase3Freshness.test_reserved_item_spoils_and_no_stock_becomes_unfulfillable) ... ok
test_reserved_item_spoils_triggers_re_reservation (tests.test_quan.TestQuanPhase3Freshness.test_reserved_item_spoils_triggers_re_reservation) ... ok
test_headless_quan_run_phase3_preset (tests.test_quan.TestQuanPhase3InventoryContract.test_headless_quan_run_phase3_preset) ... ok
test_read_and_write_inventory_v12_itemized (tests.test_quan.TestQuanPhase3InventoryContract.test_read_and_write_inventory_v12_itemized) ... ok
test_read_inventory_v12_rejects_dict_count_returns_bad_input (tests.test_quan.TestQuanPhase3InventoryContract.test_read_inventory_v12_rejects_dict_count_returns_bad_input) ... ok
test_cook_started_locks_price_by_average_freshness (tests.test_quan.TestQuanPhase3PricingAndCooking.test_cook_started_locks_price_by_average_freshness) ... ok
test_tip_calculated_on_locked_base_price (tests.test_quan.TestQuanPhase3PricingAndCooking.test_tip_calculated_on_locked_base_price) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.308s

OK
```
