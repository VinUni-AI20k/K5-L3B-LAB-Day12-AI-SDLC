# Bằng chứng triển khai Module sim/quan (Phase 2 - Test Contract v1.1)

**Người thực hiện:** Nguyễn Văn Lâm (`sim/quan` · Integrator)  
**Nhánh:** `codex/quan-phase-2`  
**Phạm vi:** 
- [game.contract.json](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/game.contract.json)
- [chonoi/sim/quan.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/sim/quan.py)
- [chonoi/contract.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/contract.py)
- [chonoi/inventory.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/inventory.py)
- [chonoi/scenario.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/chonoi/scenario.py)
- [tests/test_quan.py](file:///e:/Projects/Lab12Vinuni/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/tests/test_quan.py)

---

## 1. Các hạng mục đã hoàn thành theo TICKET-02 (Phase 2)

1. **Hợp đồng và cấu hình v1.1:**
   - Cập nhật `contract_version: "1.1"` trong `game.contract.json`.
   - Cấu hình chuẩn Quán:
     - 2 bếp: `B1 [2, 8]`, `B2 [5, 8]`.
     - 4 bàn: `T1 [9, 2]`, `T2 [13, 2]`, `T3 [9, 6]`, `T4 [13, 6]`.
     - 6 món menu: `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`, `canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam`.
     - 2 nguyên liệu mới: `ca_keo` (cá kèo), `keo_neo` (kèo nèo) trong `inventory.py` và `scenario.py`.
     - Cấu hình `day_plan` cho 5 ngày (D1–D5) và `shop` nâng cấp (`oxygen`, `hp`).

2. **Luật chơi Quán Phase 2 (`QuanSim`):**
   - **Xếp chỗ:** Khách mới đến ghế trống có ID nhỏ nhất (`T1` < `T2` < `T3` < `T4`).
   - **Kế hoạch Ngày (`day_plan`):** Trong chế độ `day`, khách chỉ chọn các món có trong kế hoạch `day_plan["dishes"]` mà đủ nguyên liệu khả dụng. Quán chạy độc lập dùng cả 6 món.
   - **Ưu tiên bếp:** Bếp `idle` nhận đơn `reserved` cũ nhất theo thứ tự `(order_tick, table_id, order_id)`.
   - **Tính boa chuẩn:** `floor(base_price * 0.2)` khi kiên nhẫn lúc giao $\ge 50\%$. Thu boa dương cộng $0.2$ uy tín.
   - **Đóng ca chuẩn:** Khách đang ăn thanh toán ngay (`paid`, reason: `closing`), khách đang chờ rời đi không trừ uy tín (`customer_left`, reason: `closing`). Dọn món ở bếp và tay.
   - **Mở rộng Cháy món (`burn`):** Khi cấu hình `burn_s`, nếu `ready_ticks > burn_s * 60`, món bị cháy (`dish_burnt`), bếp rảnh ngay, thử cấp lại `reserved` hoặc chuyển sang `unfulfillable`.

---

## 2. Kết quả kiểm thử

### Lệnh chạy:
```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -v
python3 tools/check_team.py
python3 -m chonoi.headless --mode quan --seed 1 --ticks 150 --inventory docs/contracts/inventory.sample.json --out quan.jsonl
```

### Kết quả:
- **48/48 test PASSED (OK)**.
- Kiểm tra danh sách thành viên `check_team.py` đạt 4 thành viên (`bomgoa1102`, `lam2121`, `Hungnd1208`, `MN-HD`).
- Headless Quán chạy mượt mà, ghi nhận 2 bếp và 4 bàn trong snapshot, JSONL tất định 100%.
