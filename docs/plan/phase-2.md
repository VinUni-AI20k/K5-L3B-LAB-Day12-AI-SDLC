# Kế hoạch Phase 2 (1:00 – 1:55 · Test Contract v1.1)

- **Mục tiêu:** Nâng cấp sang `contract_version: "1.1"` với số liệu chuẩn (6 nguyên liệu, 6 món, 2 bếp, 4 bàn), cá bơi & sinh theo lịch, Cá Sấu Năm Chèo, vòng ngày `--mode day --days 1..5`, Shop (`oxygen`/`hp`), Pause 3 mode, Menu & HUD v1.1; đạt smoke tích hợp phút 20, regression P1 xanh, retro P2 và đẩy tag `phase-2` trước **1:55**.
- **Phân công chi tiết:** xem [`phase-2-task.md`](../../phase-2-task.md):
  - **M6 (`K0heii`):** `M6.1`–`M6.3` nâng `game.contract.json` (`1.1`), `contract.py`, `inventory.py`, `inputs.py`, `headless.py`, `scenario.py`; smoke tích hợp phút 20, regression P1, `verification/phase-2.md`, retro P2, gắn tag `phase-2`.
  - **M1 (`huyvu-03`):** Cá Sấu Năm Chèo (`M1`, `M2`), `patrol`/`chase`/`recoil`, `monster_hit`, rơi 1/2 giỏ LIFO, `invuln_ticks`, `faint cause:"monster"`.
  - **M2 (`QuangNEU`):** Cá bơi 1.5 m/s, phản xạ mép/góc, đổi hướng 120 tick, sinh cá 360 tick (`fish_spawned`, trần 12), nút N5/N6, `ca_keo`/`keo_neo`.
  - **M3 (`ththanh8888`):** Quán 2 bếp B1–B2, 4 bàn T1–T4, 6 món, lọc menu theo `day_plan` trong `day`.
  - **M4 (`NhMinh-2610`):** Đã hoàn thiện phần lớn `day.py`, `shop.py`, Pause trong `runner.py`; ghép với M1/M2/M3 bản v1.1 và chạy test nhiều ngày.
  - **M5 (`thanhvu101`):** Menu chính, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, Pause overlay, HUD v1.1 (`"Thủy quái!"`, `"Hết hơi!"`, Shop UI).
- **Rủi ro & giảm thiểu:**
  - `gather.py` dùng chung giữa M1 (Cá Sấu) & M2 (cá bơi/sinh) → tách helper riêng (`monsters.py`/`fish.py`) hoặc merge tuần tự nhanh.
  - Test P1 cũ kiểm cứng `fish_initial == 6` và `--mode day` trả mã `2` → đã cập nhật theo số chuẩn v1.1 và ghi rõ lý do trong `docs/clarify.md`.

## Spec M3 — Quán v1.1: 4 bàn, 2 bếp, 6 món, lọc món theo kế hoạch ngày (`ththanh8888`)

Code: `chonoi/sim/quan_customers.py` (+ tham số `allowed_dishes` của `QuanSim`). Test: `tests/test_quan_m3_v11.py` (dựng `QuanSim` trực tiếp với `game.contract.json` v1.1) và các test M3 của Phase 1 đã cập nhật.

| AC | Nội dung (`Ticket02.md` mục 1.3, 2) |
|---|---|
| AC-P2-C1 | Khách đến theo lịch `120 + 900·k` ngồi bàn trống có id nhỏ nhất trong T1–T4; bàn vừa trống (khách rời / trả tiền) được dùng lại ngay từ lượt sau; hết bàn thì bỏ lượt, không phát `no_dish` |
| AC-P2-C2 | 6 món đúng công thức, thời gian nấu, giá lấy từ dữ liệu, không hard-code; `lau_mam` giữ đủ 4 loại nguyên liệu và chỉ gọi được khi đủ cả 4 |
| AC-P2-C3 | Giữ chỗ cộng dồn giữa nhiều khách chờ: kho khả dụng = tồn − tổng phần giữ; hết thì `no_dish` dù tồn vật lý còn |
| AC-P2-C4 | Trong `day`, thực đơn khách được gọi bị lọc theo id món trong kế hoạch **trước**, rồi mới lọc theo nguyên liệu khả dụng; món ngoài kế hoạch không bao giờ được gọi dù đủ nguyên liệu |
| AC-P2-C5 | Không đếm số suất: số suất kế hoạch chỉ dùng tính mục tiêu thu gom; khách vẫn gọi tiếp món đủ nguyên liệu sau khi đã bán đủ số suất dự kiến |
| AC-P2-C6 | Quán chạy riêng (không `day`) dùng cả 6 món; có bàn trống mà không món nào đủ nguyên liệu thì `no_dish` |
| AC-P2-C7 | Hồi quy Phase 1: `allowed_dishes=None` cho kết quả y hệt trước; cùng seed → output giống từng byte; test Phase 1 chỉ đổi vì luật mới và có ghi lý do |

**Giao diện cho M4 (`day`)** — thực tế `day.py` lọc bằng `tuning.menu` đã lọc (cùng kết quả); tham số dưới đây là phương án thay thế, hiện chưa dùng: `QuanSim(tuning, scenario, streams, ids, inventory=None, allowed_dishes=None)`. `allowed_dishes` là tập id món của kế hoạch ngày (set/list/tuple), `None` = cả menu, id ngoài menu → `BadInput` (mã 2). Khách dựng sẵn từ `scenario.customers` không bị lọc.

### Test Phase 1 đổi vì luật v1.1 (hồi quy P1, M3.2b)

| Test | Vì sao đổi | Thay bằng |
|---|---|---|
| `test_quan_customers_m3::test_c5_no_free_table_skips_round` | Phase 1 chỉ có T1 nên lượt 1020 hết bàn; v1.1 có T2–T4 | `test_c5_all_tables_busy_skips_round` (chiếm đủ 4 bàn bằng fixture) |
| `test_quan_customers_m3::test_c5_table_freed_by_patience_gets_next_round` | Lượt 1020/1920/2820 giờ có bàn trống nên thành `no_dish` thay vì bỏ lượt | `test_c5_reservation_released_by_patience_lets_next_round_order` |
| `test_m3_m4_integration::test_stock_is_consumed_once_and_next_round_sees_empty_stock` | `no_dish` xuất hiện ở 1020 và 1920 (không chỉ 1920), xen vào trước `paid` | so chuỗi sự kiện bỏ `no_dish`; `no_dish` = [1020, 1920] |
| `test_m3_m4_integration::test_table_is_freed_after_paid_and_second_customer_arrives` | Khách thứ 2 vào T2 lúc 1020 thay vì T1 lúc 1920 | `test_second_customer_takes_next_free_table_and_holds_leftover_stock` |
| `test_quan_m4::test_ac_m4_01_interact_edge_and_tiebreak_no_fallback` *(của M4, chưa sửa)* | Bếp B2 mới ở [5,8] cách điểm thử [3.51,8] chỉ 1.49 m ≤ 1.5 nên vẫn tương tác được | Cần M4 dời điểm thử (ví dụ [3.51, 7] hoặc đổi vị trí B2 trong fixture) |
