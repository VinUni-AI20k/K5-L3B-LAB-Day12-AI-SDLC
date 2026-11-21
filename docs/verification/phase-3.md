# Ma trận truy vết Phase 3 — Ticket-03 "Mùa Nước Nổi" (contract v1.2)

**Nguồn:** `phase3.md` (Ticket-03). PRD không đánh mã AC nên nhóm tự đặt `AC-P3-xx` theo từng luật của ticket.
**Test của QA:** `tests/test_fresh_p3.py` (28 test, mã `test_ac_p3_xx_*`). Mọi test mang `@pending("...")`: skip mặc định để `main` xanh,
chạy thật bằng `QA_STRICT=1`. Lát nào xong và test xanh thì QA bỏ `@pending` đúng test đó.
**Cách kiểm chứng chung:** `python .agents/skills/verify-phase/verify.py --phase 3` (gom bằng chứng) và `python tools/run_checks.py` (kiểm nhanh).

**Trạng thái hiện tại (ghi trung thực):** test đã viết, chạy `QA_STRICT=1` thì **27/28 đỏ**, đều vì `main` chưa có kho cá thể
(headless báo `hold phải là mảng id...` hoặc chấp nhận kho đếm cũ mà v1.2 phải trả mã 2). Chưa có lát nào của Phase 3 vào `main`.
Cột "Cần lát" cho biết test chờ phần nào; "Kết quả" cập nhật theo bằng chứng chạy trên commit gắn tag.

## Độ tươi và kho cá thể

| AC | Luật (Ticket-03) | Test | Cần lát | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | Ươn khi fresh < 30, so ngưỡng trước làm tròn; ví dụ ticket: fresh 30 → `spoiled` ở tick 1; fresh 30.5 → ươn ở bước 61 | `Threshold.*` | gather | chờ |
| AC-P3-02 | `spoiled` đúng một lần; nhiều cá thể cùng vượt ngưỡng phát theo id | `SpoiledOnce.*` | gather | chờ |
| AC-P3-03 | Giỏ hao 0.5/s; hàng mới fresh = 100, hao từ bước sau | `GatherDecay.*` | gather | chờ |
| AC-P3-04 | Id `I1, I2...` theo thứ tự vào giỏ, không tái dùng; hàng ươn vẫn chiếm ô (`hold_full`) | `GatherIds.*` | gather | chờ |
| AC-P3-05 | Ngất: `lost` là mảng cá thể LIFO, `gather_end.inventory` và file kho `{"items":[]}` | `GatherLoss.*` | gather | chờ |
| AC-P3-06 | `--inventory-out` ghi theo id, khớp `gather_end.inventory`; chạm `--ticks` trước kết thúc thì không tạo file | `FileOut.*` | gather + adapter | chờ |
| AC-P3-07 | Smoke hai tiến trình giữ id, kind, fresh; quán nhận cả hàng ươn; kho đếm cũ / sai schema / scenario đếm cũ → mã 2 | `Handoff.*` | adapter (`inventory.py`, `scenario.py`) | chờ |
| AC-P3-08 | `day`: bàn giao cùng tick, hàng không hao thêm; Ngày kế cấp id mới theo thứ tự mảng | `DayHandoff.test_ac_p3_08_*` | day (lát 5) | chờ |
| AC-P3-09 | Shop giữ kho cá thể, hàng thô ở Shop không hao | `DayHandoff.test_ac_p3_09_*` | day (lát 5) | chờ |
| AC-P3-10 | Pause dừng hao tươi | `PauseFresh.*` | gather | chờ |
| AC-P3-11 | Kho quán hao 0.25/s, kể cả hàng đang giữ chỗ | `QuanDecay.*` | quán (lát 4) | chờ |
| AC-P3-12 | Giữ chỗ theo id: tươi nhất, hòa id nhỏ; cấp theo `order_tick` rồi id bàn; khách mới giữ cá thể tươi nhất | `ReserveById.*` | quán (lát 3) | chờ |
| AC-P3-13 | Giữ chỗ vừa ươn: nhả hết và thử giữ lại đúng một lần; không đủ → `unfulfillable`, khách vẫn chờ | `SpoilRetry.*` | quán (lát 3) | chờ |
| AC-P3-14 | `base_price = floor(giá niêm yết × TB fresh các cá thể dùng / 100)` khi bắt đầu nấu; `cook_started.items` là mảng cá thể | `PriceByFreshness.test_ac_p3_14_*` | quán (lát 4) | chờ |
| AC-P3-15 | Boa = floor(giá đã chốt × 0.2) | `PriceByFreshness.test_ac_p3_15_*` | quán (lát 4) | chờ |
| AC-P3-16 | Hàng ươn không dùng nấu: không món đủ → `no_dish` | `SpoiledNotCookable.*` | quán (lát 3) | chờ |
| AC-P3-17 | Fixture giữ chỗ mâu thuẫn (id lạ, trỏ hàng ươn, sai công thức, dùng chung, kiểu cũ, id trùng) → mã 2 | `FixtureValidation.*` | adapter + quán | chờ |

## HUD, hồi quy và tài liệu

| AC | Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|---|
| AC-P3-18 | HUD cho người chơi đọc được độ tươi hoặc nhận ra hàng ươn | `chonoi/web/index.html`: thanh tươi + gạch chéo hàng ươn ở giỏ; kho quán hiện "tươi N, k ươn", kho khả dụng bỏ hàng ươn và phần giữ chỗ, cảnh báo ươn. Đã vẽ thử bằng canvas giả với snapshot v1.1 và v1.2 (đúng cả hai). | đạt ở mức vẽ thử; chưa chơi thật vì chưa có dữ liệu v1.2 |
| AC-P3-19 | Hồi quy P1–P2 còn hiệu lực đạt; test cũ bị luật mới thay phải ghi lý do | ~10 file test dựa vào kho đếm: `test_gather_p1`, `test_quan_p1`, `test_day_p2`, `test_lat2`, `test_quan_lat3`, `test_quan_lat4`, `test_gather_lat1`, `test_smoke_p1`, `test_lat0_v11`, `test_python_starter_units`. Bảng "giữ / đổi / thêm" sẽ ghi ở đây khi v1.2 vào `main`. | chờ |
| AC-P3-20 | `CHANGELOG.md` ghi breaking change và cách cập nhật fixture | [CHANGELOG.md](../../CHANGELOG.md) (mục "Dự kiến v1.2") | bản nháp, cập nhật khi v1.2 bật |
| AC-P3-21 | Bằng chứng ở `docs/proof/phase-3/` khớp commit gắn tag; `contract_version: "1.2"` | `verify-phase --phase 3` | chờ |

## Điều QA cần từ nhóm
- **Việc schema/adapter chưa có chủ** (`inventory.py`, `contract.py` khóa `freshness`, `scenario.py` mảng cá thể). Thiếu nó thì mọi test trên không có gì để xanh.
- **Mở rộng (Khách đặt trước, Dòng nước lũ):** nhóm chưa chọn. Test QA chỉ phủ lõi; `random_reservations`, `current` không dùng trong fixture lõi.
- **Giả định của test cần PO xác nhận với Anh Năm** (ghi `docs/clarify.md`): `spoiled` ghi `phase` của pha chứa cá thể (gather: `"gather"`); file kho ghi `fresh` dạng số thập phân đủ chính xác (test so với dung sai ±0.01).
