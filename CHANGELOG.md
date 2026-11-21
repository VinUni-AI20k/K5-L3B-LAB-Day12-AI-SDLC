# Changelog

## [Unreleased — Phase 3 (`v1.2`, tag `phase-3`)]
### Breaking Changes
- **Schema file kho `v1.2` (`inventory.json`, `gather.hold`, `quan.stock`, `customers[].reserved`):**
  - Chuyển từ kho đếm số lượng (`{"items": {"ca_loc": 2}}`) sang **danh sách cá thể có độ tươi** (`{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`).
  - `customers[].reserved` chuyển sang mảng `id` cá thể (ví dụ `["I1"]`), giữ theo độ tươi cao nhất và hòa theo `id`.
  - File kho hoặc scenario dùng map đếm kiểu cũ bị từ chối với mã thoát `2`.
- **Cách cập nhật fixture cũ:** thay mảng chuỗi ở `gather.hold` thành `[{"id": "I1", "kind": "...", "fresh": 100}]` và `quan.stock` tương tự; đơn `reserved` dùng danh sách id cá thể chưa ươn (`fresh >= 30`).

### Added
- **Độ tươi & ngưỡng ươn (`tuning.freshness`):** tính theo đơn vị nguyên `240/điểm` (`gather -2/tick`, `quan -1/tick`, ngưỡng ươn `< 30`), phát `spoiled` theo thứ tự `id`, tái giữ chỗ một lần hoặc chuyển `unfulfillable`, chốt `base_price = floor(price * avg_fresh / 100)` lúc bắt đầu nấu.
- **Mở rộng `burn` (`extensions: ["burn"]`):** `quan.burn_s = 20` (`1200` tick); quá `1200` tick món chín phát `dish_burnt`, bếp rảnh và thử tái giữ chỗ ngay cho khách.
- Hiển thị `%` tươi, cảnh báo `ƯƠN` và thanh đếm cháy trên UI [chonoi/web/index.html](chonoi/web/index.html).

## [Phase 2 (`v1.1`, tag `phase-2`)]
### Added
- Số liệu chuẩn `v1.1`: 6 nguyên liệu, 6 món, 2 bếp `B1–B2`, 4 bàn `T1–T4`, `day_plan` D1–D5, `shop` nâng cấp `oxygen`/`hp`.
- Cá bơi `1.5 m/s`, đổi hướng bước `120`, phản xạ mép, sinh thêm mỗi `360` tick (trần 12) và thủy quái `ca_sau` (`M1`/`M2`).
- Vòng lặp 5 ngày (`DaySim`), `ShopSim`, `pause`/`resumed` cả 3 chế độ.
- Chi tiết tích hợp Gather `v1.1` và bằng chứng TV2 tại `docs/proof/phase-2/member-2/`.

## [Phase 1 (`v1.0`, tag `phase-1`)]
### Added
- Chế độ Lặn & Hái (`gather`) và Mở Quán (`quan`) chuẩn hóa đầy đủ PRD-0 E/F/G, cùng 6 thành viên hợp lệ trong `TEAM.md`.
