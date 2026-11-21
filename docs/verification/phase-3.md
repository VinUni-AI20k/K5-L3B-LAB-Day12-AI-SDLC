# Ma trận truy vết Phase 3 — Ticket-03 "Mùa Nước Nổi" (contract v1.2)

**Nguồn:** `phase3.md` (Ticket-03). PRD không đánh mã AC nên nhóm tự đặt `AC-P3-xx` theo từng luật của ticket.
**Test của QA:** `tests/test_fresh_p3.py` (28 test, mã `test_ac_p3_xx_*`). Chạy với manifest v1.2 tạm (`tests/qa_helpers.use_v12_manifest`,
cùng cách lát 0) vì `game.contract.json` trên `main` còn v1.1; khi manifest lên v1.2 hàm này tự thành no-op.
Test chờ lát chưa merge mang `@pending("...")`: skip mặc định để `main` xanh, chạy thật bằng `QA_STRICT=1`.
**Cách kiểm chứng chung:** `python .agents/skills/verify-phase/verify.py --phase 3` (gom bằng chứng) và `python tools/run_checks.py` (kiểm nhanh).

**Trạng thái hiện tại (ghi trung thực, đo trên `main` @ `c909a12` + nhánh sửa `fix/p3-qa-day`):**
- `QA_STRICT=1`: **22/28 đạt, 6/28 chưa đạt.** 6 test chưa đạt đều là hao tươi + `spoiled` của **gather** (AC-P3-01, 02, 03, 10), lát gather chưa merge.
- "đạt" nghĩa là chạy xanh trên **manifest v1.2 tạm**, chưa phải manifest chính. Bằng chứng ở commit gắn tag cần chạy lại sau khi v1.2 được bật.
- Suite thường (v1.1): **233 test OK** (6 skip là 6 test pending ở trên).

## Độ tươi và kho cá thể

| AC | Luật (Ticket-03) | Test | Cần lát | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | Ươn khi fresh < 30, so ngưỡng trước làm tròn; ví dụ ticket: fresh 30 → `spoiled` ở tick 1; fresh 30.5 → ươn ở bước 61 | `Threshold.*` | gather | **chưa đạt**: gather chưa có hao tươi và `spoiled` (test đỏ khi `QA_STRICT=1`) |
| AC-P3-02 | `spoiled` đúng một lần; nhiều cá thể cùng vượt ngưỡng phát theo id | `SpoiledOnce.*` | gather | **chưa đạt**: gather chưa có hao tươi và `spoiled` (test đỏ khi `QA_STRICT=1`) |
| AC-P3-03 | Giỏ hao 0.5/s; hàng mới fresh = 100, hao từ bước sau | `GatherDecay.*` | gather | **chưa đạt**: gather chưa có hao tươi và `spoiled` (test đỏ khi `QA_STRICT=1`) |
| AC-P3-04 | Id `I1, I2...` theo thứ tự vào giỏ, không tái dùng; hàng ươn vẫn chiếm ô (`hold_full`) | `GatherIds.*` | gather | đạt (manifest v1.2 tạm) |
| AC-P3-05 | Ngất: `lost` là mảng cá thể LIFO, `gather_end.inventory` và file kho `{"items":[]}` | `GatherLoss.*` | gather | đạt (manifest v1.2 tạm) |
| AC-P3-06 | `--inventory-out` ghi theo id, khớp `gather_end.inventory`; chạm `--ticks` trước kết thúc thì không tạo file | `FileOut.*` | gather + adapter | đạt (manifest v1.2 tạm) |
| AC-P3-07 | Smoke hai tiến trình giữ id, kind, fresh; quán nhận cả hàng ươn; kho đếm cũ / sai schema / scenario đếm cũ → mã 2 | `Handoff.*` | adapter (`inventory.py`, `scenario.py`) | đạt (manifest v1.2 tạm) |
| AC-P3-08 | `day`: bàn giao cùng tick, hàng không hao thêm; Ngày kế cấp id mới theo thứ tự mảng | `DayHandoff.test_ac_p3_08_*` | day (lát 5, `day.py`: chuyển nguyên mảng cá thể, Ngày kế cấp id mới) | đạt (manifest v1.2 tạm) |
| AC-P3-09 | Shop giữ kho cá thể, hàng thô ở Shop không hao | `DayHandoff.test_ac_p3_09_*` | day (lát 5, `shop.py`: giữ kho cá thể, không hao) | đạt (manifest v1.2 tạm) |
| AC-P3-10 | Pause dừng hao tươi | `PauseFresh.*` | gather | **chưa đạt**: gather chưa có hao tươi và `spoiled` (test đỏ khi `QA_STRICT=1`) |
| AC-P3-11 | Kho quán hao 0.25/s, kể cả hàng đang giữ chỗ | `QuanDecay.*` | quán (lát 4) | đạt (manifest v1.2 tạm) |
| AC-P3-12 | Giữ chỗ theo id: tươi nhất, hòa id nhỏ; cấp theo `order_tick` rồi id bàn; khách mới giữ cá thể tươi nhất | `ReserveById.*` | quán (lát 3) | đạt (manifest v1.2 tạm) |
| AC-P3-13 | Giữ chỗ vừa ươn: nhả hết và thử giữ lại đúng một lần; không đủ → `unfulfillable`, khách vẫn chờ | `SpoilRetry.*` | quán (lát 3) | đạt (manifest v1.2 tạm) |
| AC-P3-14 | `base_price = floor(giá niêm yết × TB fresh các cá thể dùng / 100)` khi bắt đầu nấu; `cook_started.items` là mảng cá thể | `PriceByFreshness.test_ac_p3_14_*` | quán (lát 4) | đạt (manifest v1.2 tạm) |
| AC-P3-15 | Boa = floor(giá đã chốt × 0.2) | `PriceByFreshness.test_ac_p3_15_*` | quán (lát 4) | đạt (manifest v1.2 tạm) |
| AC-P3-16 | Hàng ươn không dùng nấu: không món đủ → `no_dish` | `SpoiledNotCookable.*` | quán (lát 3) | đạt (manifest v1.2 tạm) |
| AC-P3-17 | Fixture giữ chỗ mâu thuẫn (id lạ, trỏ hàng ươn, sai công thức, dùng chung, kiểu cũ, id trùng) → mã 2 | `FixtureValidation.*` | adapter + quán | đạt (manifest v1.2 tạm) |

## HUD, hồi quy và tài liệu

| AC | Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|---|
| AC-P3-18 | HUD cho người chơi đọc được độ tươi hoặc nhận ra hàng ươn | `chonoi/web/index.html`: thanh tươi + gạch chéo hàng ươn ở giỏ; kho quán "tươi N, k ươn", kho khả dụng bỏ hàng ươn và phần giữ chỗ, cảnh báo ươn. Đã vẽ thử bằng canvas giả với snapshot v1.1 và v1.2. | đạt ở mức vẽ thử với snapshot giả; **chưa chơi thật** trên `chonoi.live` bản v1.2 (gather chưa có hao tươi nên giỏ chưa ươn thật) |
| AC-P3-19 | Hồi quy P1–P2 còn hiệu lực đạt; test cũ bị luật mới thay phải ghi lý do | Đo bằng cách chạy cả suite với manifest v1.2 tạm. **v1.1 (`main`): 233 OK.** **Khi bật v1.2: 56 test vỡ ở 12 file** (bảng dưới). Nguyên nhân chung: fixture/assert viết theo kho đếm (`"hold": ["ca_loc"]`, `"stock": {"ca_loc": 1}`, `reserved` là map) mà Ticket-03 đổi sang mảng cá thể. Đây là đổi do luật mới, không phải lỗi luật. | **chưa đạt**: nợ hồi quy chờ bật v1.2. `test_day_p2` (QA) đã sửa chạy được cả hai phiên bản |
| AC-P3-20 | `CHANGELOG.md` ghi breaking change và cách cập nhật fixture | [CHANGELOG.md](../../CHANGELOG.md): bảng trước/sau, cách đổi fixture, danh sách test vỡ | đạt (nội dung); cập nhật số liệu khi bật v1.2 |
| AC-P3-21 | Bằng chứng ở `docs/proof/phase-3/` khớp commit gắn tag; `contract_version: "1.2"` | `verify-phase --phase 3` | **chưa đạt**: manifest chính còn `"1.1"`; chưa gắn tag |

### AC-P3-19 — test cũ vỡ khi bật v1.2 (56 test, 12 file) và người sở hữu theo `docs/plan/phase-3.md`

| File test | Vỡ | Người đổi (theo plan) | Lý do |
|---|---|---|---|
| `test_quan_lat3.py` | 11 | trongnghia2304 | khách/`reserved` dùng map kind → số; v1.2 là mảng id |
| `test_quan_p1.py` | 10 | trongnghia2304, nguyenhung1901 (QA có thể hỗ trợ) | `stock` map, `reserved`, giá niêm yết |
| `test_gather_p1.py` | 7 | mhoo40, s0ra1n0 (QA có thể hỗ trợ) | `hold` mảng kind, `lost`, `gather_end.inventory` |
| `test_quan_lat4.py` | 6 | nguyenhung1901 | bếp trừ kho theo lượng, `cook_started.items`, giá |
| `test_lat2.py` | 5 | mhoo40 | hái/bắt cá thêm vào giỏ dạng kind |
| `test_quan_p2.py` | 4 | trongnghia2304 / nguyenhung1901 | kho quán Phase 2 theo lượng |
| `test_gather_lat1_p2.py` | 4 | s0ra1n0 | giỏ, `lost` |
| `test_gather_lat1.py` | 3 | s0ra1n0 | giỏ ngất |
| `test_smoke_p1.py`, `test_lat0_v11.py`, `test_python_starter_units.py`, `test_p2_lat2_fish.py` | 2 + 2 + 1 + 1 | s0ra1n0 (adapter) / mhoo40 | file kho đếm → mã 2; scenario kho đếm |
| `test_day_p2.py` (QA) | 0 | tiepnnk01-10 — **đã sửa** | fixture đổi qua `mk_hold` / `mk_stock` / `stock_counts` nên đúng ở cả v1.1 và v1.2 |

## Điều QA cần từ nhóm
- **Lát gather:** hao tươi giỏ 0.5/s + `spoiled` (AC-P3-01, 02, 03, 10). Khi merge, QA bỏ 6 `@pending` còn lại.
- **Bật v1.2 trong `game.contract.json`:** phải đi cùng PR sửa 56 test ở bảng trên, nếu không `main` đỏ. Chưa có lát nào nhận việc này.
- **Mở rộng (Khách đặt trước, Dòng nước lũ):** nhóm chưa chọn; test QA chỉ phủ lõi.
- Hai giả định của test đã được Ticket chốt: `spoiled` mang `phase` của pha đang chạy (clarify #15); `fresh` ghi đủ chính xác, quan sát ±0.01 (clarify #16).
