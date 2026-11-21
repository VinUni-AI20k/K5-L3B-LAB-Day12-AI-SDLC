# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | minhtriet061203 | Lát 3: khách theo lịch, chọn món, giữ chỗ, kiên nhẫn/uy tín, fixture + mã 2; đã khớp hợp đồng + PRD-0 mục D/F; 61/61 test xanh | Review lát 4 của len2412 (dùng `_release`, `order_status`) | Clarify #9 (khách đang ăn có giảm kiên nhẫn) còn là giả định |
| 1 | BLong1501 | Lát 2 `sim/gather` (`AC-P1-20..23`), 16 test hộp đen (48/48 xanh, tất định 12/12, smoke 10/10), HUD `chonoi/web/index.html` (`AC-P1-53`) | Tạo PR gộp `slice2-gather` vào `main`, review chéo Lát 1 (`LyLe10`) | Không |
| 1 | len2412 | Lát 4: bếp, interact, phục vụ, thanh toán và đóng ca; thêm test hồi quy | Chạy tests/smoke/tất định và rà cùng lát 3 khi Python sẵn có | Python 3 không có trên PATH; kết quả lệnh chi tiết ở proof phase-1 |
| 2 | minhtriet061203 | AC-P2-31 (4 bàn, 6 món) + AC-P2-32 (`menu_filter` theo `day_plan`); 111/111 test xanh | Pair với lát 4 (runner `day`) để gọi `QuanSim(…, menu_filter=day_plan[day].dishes, money, earned, reputation)` | Chờ PO xác nhận clarify #16 |
| 2 | BLong1501 | Lát 1 P2 (`AC-P2-10..14`): cá bơi 1.5 m/s, phản xạ mép/góc, sinh tại `360·k`, 7 test `test_gather_p2_fish.py`, HUD sáng v1.1; 100/100 test + tất định + smoke đạt | Tạo PR `p2-slice1-fish-hud` → `main`, hỗ trợ/review lát 2 (`LyLe10`) | Không |
| 3 | minhtriet061203 | Quán v1.2: kho cá thể, hao tươi, `spoiled`, giữ theo id, giữ lại một lần → `unfulfillable`, fixture; 196/196 xanh (manifest vẫn v1.1) | PR `slice3-p3`; pair với len2412 rà `_cook_at` + giá theo tươi; bật v1.2 cùng nhóm ở p25 | Clarify #17, #18 chờ PO |
