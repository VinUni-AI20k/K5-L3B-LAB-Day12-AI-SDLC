# ADR-0001: Đổi kho đếm sang kho cá thể có độ tươi (Test Contract v1.2)

- Trạng thái: chấp nhận
- Ngày, người quyết: 21/11/2026, LeBao403 (Integrator), theo Change Request Ticket-03 "Mùa Nước Nổi"

## Bối cảnh

Ticket-03 đổi kho từ đếm theo loại `{"items": {"ca_loc": 1}}` sang mảng cá thể `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`. Mỗi nguyên liệu có id riêng (`I1, I2, …`, tăng xuyên pha và Ngày) và độ tươi hao theo thời gian (giỏ 0.5/s, kho quán 0.25/s). Hàng có `fresh < 30` là hàng ươn, không dùng nấu được. Giữ chỗ chuyển từ theo lượng sang theo id. Giá món chốt theo độ tươi trung bình.

Thay đổi này đụng mọi lát: file kho, scenario, giỏ (B), giữ chỗ và vòng ngày (C), kho và bếp (D), HUD (E). Nếu bật v1.2 cùng lúc ở mọi nơi thì `main` sẽ đỏ cho tới khi mọi người xong.

## Các lựa chọn đã cân nhắc

1. Bật v1.2 ngay trong một PR lớn: nhanh nhưng `main` đỏ lâu, các lát phải chờ nhau.
2. Mỗi lát tự chuyển và tự bật: dễ lệch schema giữa hai đầu bàn giao.
3. **Nền hai phiên bản rồi bật một lần:** Integrator làm adapter đọc/ghi được cả hai schema, chọn theo `contract_version`. Các lát chuyển song song dưới manifest 1.1, khi xong thì Integrator bật 1.2 một lần.

## Quyết định

Chọn lựa chọn 3.

- `contract_version` nhận `"1.1"` và `"1.2"`. v1.2 bắt buộc `tuning.freshness = {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`; v1.1 cấm khối này. Code chọn đường v1.2 bằng `chonoi.fresh.enabled(tuning)` (có khối `freshness`).
- Độ tươi tính bằng số nguyên: 240 đơn vị mỗi điểm. Giỏ trừ 2 đơn vị/tick, kho quán trừ 1 đơn vị/tick, ươn khi dưới 7200. So ngưỡng và phép floor không phụ thuộc sai số dấu phẩy động.
- Cá thể trong code là `{id, kind, u}`; ra ngoài (snapshot, event, file kho) là `{id, kind, fresh}` qua `fresh.public`.
- File kho v1.2 sắp theo id, ghi `fresh` bằng repr đầy đủ (không làm tròn như JSONL). Đọc ở v1.2 mà gặp kho đếm hoặc sai schema thì mã 2.
- Một `IdAllocator` cho cả lượt; id trong fixture được `reserve` để id mới nối tiếp.

## Thứ tự tích hợp

1. Nền hai phiên bản (LeBao403): `chonoi/fresh.py`, `inventory.py`, `contract.py`, phần hold/stock của `scenario.py`, `headless.py`, `runner.py`, khung `GatherSim`/`QuanSim`. Manifest giữ 1.1, toàn bộ test cũ vẫn xanh.
2. Song song: B chuyển giỏ, C chuyển giữ chỗ và vòng ngày, D chuyển kho và bếp, E làm HUD. Mỗi người chuyển test của mình.
3. Smoke bàn giao kho trên bản tích hợp ở phút 20.
4. Integrator bật `contract_version: "1.2"` khi các lát đã gộp. E sửa test chung theo schema mới, ghi lý do.
5. Smoke file và day, regression P1-P2, CHANGELOG, verification, tag `phase-3`.

## Hệ quả

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter, schema | `game.contract.json`, `chonoi/fresh.py` (mới), `contract.py`, `inventory.py`, `scenario.py` (hold/stock), `headless.py`, `runner.py` | Thêm `test_p3_fresh_schema.py`; khi bật 1.2 đổi `test_gather_lat1.py`, `test_p2_nen_v11.py`, `test_p2_monsters.py`, `test_p2_snake.py` | LeBao403 |
| Lặn (giỏ) | `chonoi/sim/gather.py`: `_decay_hold`, `_try_harvest`, `_try_catch` | `test_gather_lat2.py`, test cá; thêm test độ tươi giỏ | B |
| Quán (khách, giữ chỗ) | `chonoi/sim/quan.py` (giữ theo id, giữ lại khi ươn), `scenario.py` (`reserved` là mảng id), `day.py`, `shop.py` | `test_lat3_khach.py`, `test_lat3_p2.py`, test day; thêm test giữ chỗ | C |
| Quán (kho, bếp, giá) | `chonoi/sim/quan.py` (hao kho, `spoiled` stock, nấu tiêu id, giá theo tươi) | `test_lat4_quan.py`, test 2 bếp; thêm test giá | D |
| HUD, QA | `chonoi/web/index.html`, `test_smoke_p1.py`, `test_e_qa_p1.py`, `CHANGELOG.md`, `docs/verification/phase-3.md` | `test_smoke_p1.py` (kho đếm thành cá thể) | E |
