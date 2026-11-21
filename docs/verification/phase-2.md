# Ma trận truy vết Phase 2 (Ticket-02, Test Contract v1.1)

- **Commit kiểm chứng:** `1542e36` (main sau "Feat: add fish moving" và PR #12). Chạy lúc 2026-11-21 12:46. Lần chạy trước ở `d424133` đã được thay bằng lần này.
- **Bằng chứng tổng:** `python .agents/skills/verify-phase/verify.py --phase 2` → [`docs/proof/phase-2/summary.md`](../proof/phase-2/summary.md): **178 test, 177 OK, 1 FAIL** (xem AC-P2-10); tất định gather/quan giống từng byte; kho gather → quan khớp; `TEAM.md` đạt.
- **Mã AC:** theo bảng mục 0b của [`docs/plan/phase-2.md`](../plan/phase-2.md). "Chưa đạt" = chưa có code, có lỗi, hoặc chưa có bằng chứng ở commit này.
- Người viết: trongnghia2304 (PO) làm thay QA vì tiepnnk01-10 đã sang Phase 3; QA review và giữ file từ đây. **s0ra1n0 chạy lại trên commit gắn tag `phase-2`** nếu còn merge thêm sau `1542e36`.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 Contract v1.1, số chuẩn, 6 nguyên liệu / 6 món, `extensions` | `tests/test_lat0_v11.py` (`ContractV11`, `KindsAndScenario`), smoke P1 cập nhật số chuẩn | [`tests.txt`](../proof/phase-2/tests.txt) | **đạt một phần**: v1.1, số chuẩn, N5/N6, 8 đàn, 3 loài cá, 6 món, kind `ca_keo`/`keo_neo` đạt. `extensions` vẫn `[]` — xem AC-P2-12 |
| AC-P2-02 Cá bơi 1.5 m/s, đổi hướng theo seed mỗi 120 bước, phản xạ mép | `tests/test_p2_lat2_fish.py`; chạy gather 1500 tick, đo quãng 1 s | [`fish.txt`](../proof/phase-2/fish.txt): F1 đi **2.086 m/s** theo hướng chéo (1.475 m mỗi trục) | **đạt một phần**: bơi, đổi hướng, phản xạ, dải độ sâu có. **Lỗi tốc độ chéo**: `_reflect_1d` (`gather.py`) dịch đủ `rem` trên **mỗi** trục, chỉ dùng dấu của thành phần vận tốc → chéo nhanh √2 lần. Sửa: truyền `rem × |thành phần|` cho từng trục — mhoo40 |
| AC-P2-03 8 đàn đầu ca, sinh mỗi 360 tick, trần 12, `fish_spawned`, cá kèo / kèo nèo | `test_lat0_v11.py::InitialFish`, `tests/test_p2_lat2_fish.py`, `KindsAndScenario::test_kind_moi_qua_kho_va_gio` | [`fish.txt`](../proof/phase-2/fish.txt): `fish_spawned` ở tick 360, 720, 1080, 1440 (F9–F12); 8 → 9 đàn ở tick 360, 12 đàn ở tick 1500 | **đạt** |
| AC-P2-04 Cá Sấu M1/M2, patrol/chase, hit, bất tử, recoil, ngất `monster` (`ai-usage-log` / `lat1.md` của lát 1 ghi nhầm là AC-P2-03) | `tests/test_gather_lat1_p2.py` (Patrol, Chase, Hit, Faint, tất định), `test_lat0_v11.py::Monsters` (M1 Ngày 1, M2 từ Ngày 3) | [`tests.txt`](../proof/phase-2/tests.txt), [`lat1.md`](../proof/phase-2/lat1.md) | **đạt** |
| AC-P2-05 Quán 2 bếp, 4 bàn, 6 món | `test_quan_lat4.py::Phase2Compatibility` + test bổ sung của lát 4, `test_quan_lat3.py` (2 test ≥ 2 bàn nay chạy) | [`tests.txt`](../proof/phase-2/tests.txt), [`lat4.md`](../proof/phase-2/lat4.md), [`lat3-p2-unittest.txt`](../proof/phase-2/lat3-p2-unittest.txt) | **đạt** |
| AC-P2-06 Mode `day` + kế hoạch D1–D5 + lọc món + Shop + cấp từ Ngày kế, một Ngày ≤ 20 s | `tests/test_day_p2.py` (`DayFlow`, `Shop`, `Validation`), `tests/test_quan_p2.py` (lọc món, có kiểm đột biến); chạy 1 Ngày đầy đủ và 5 Ngày | [`tests.txt`](../proof/phase-2/tests.txt), [`day.txt`](../proof/phase-2/day.txt): 1 Ngày 22.200 tick **1.09 s**, `--days 5` đúng D1–D5, `days_complete` | **đạt** |
| AC-P2-07 Pause ở cả 3 mode | `test_day_p2.py::Pause` | [`tests.txt`](../proof/phase-2/tests.txt) | **đạt** |
| AC-P2-08 UI: menu, DayIntro/EveningIntro/DayResult/Summary, menu pause, HUD sáng + quán | Đọc `chonoi/web/index.html`, `chonoi/live.py`; mở `chonoi.live --mode gather` trên trình duyệt | `live.py` chỉ nhận `--mode gather\|quan`; trang chạy được (HUD giờ, oxy, Máu, giỏ, nút, cá, Cá Sấu) nhưng chưa có menu / pause / màn chuyển Ngày / "Thủy quái!" | **chưa đạt** |
| AC-P2-09 Smoke tích hợp gather → quan (v1.1) | Hai lệnh mục G PRD-0 với preset v1.1 | [`integration.txt`](../proof/phase-2/integration.txt): `catch.json` = `gather_end.inventory` = stock quán tick 0 = `{"bong_sung":2,"ca_loc":1}` | **đạt** |
| AC-P2-10 Regression P1 với số chuẩn | Toàn bộ test P1 chạy với contract v1.1 | [`tests.txt`](../proof/phase-2/tests.txt): **FAIL** `test_lat2.py::test_catch_underwater_removes_fish_and_sets_cooldown` (bắt được 1 đàn thay vì 2) | **chưa đạt**: luật đúng, test cũ. Fixture khai `fish` mà không tắt `random_fish`, nên theo Ticket 4.3 cá fixture vẫn bơi; cá lóc F2 đặt ở `d = 5` ngoài dải [8, 20] nên bị đưa khỏi tầm bắt. Sửa: thêm `"random_fish": false` vào fixture, ghi lý do trong commit — mhoo40 (chủ test) |
| AC-P2-11 Tất định 3 mode | `verify.py` (gather, quan) + chạy `day` 2 lần cùng seed | [`determinism.txt`](../proof/phase-2/determinism.txt), [`day.txt`](../proof/phase-2/day.txt): giống từng byte | **đạt** |
| AC-P2-12 Mở rộng `burn` | `test_quan_lat4.py::test_burn_*` (tuning riêng `burn_s: 20`) | [`tests.txt`](../proof/phase-2/tests.txt), [`lat4.md`](../proof/phase-2/lat4.md) | **đạt một phần**: luật cháy có test. Manifest vẫn `"extensions": []`, `burn_s: null`, và **`chonoi/contract.py` dòng 291 từ chối mọi `burn_s` khác `null`** — áp quyết định I-1 cần sửa cả `contract.py` (chấp nhận `burn_s` hữu hạn khi `extensions` có `burn`) — s0ra1n0; mục "Mở rộng" trong README — nguyenhung1901 |

## Đánh giá ngắn
- **Đạt:** 7/12 (03, 04, 05, 06, 07, 09, 11). **Đạt một phần:** 3/12 (01, 02, 12). **Chưa đạt:** 2/12 (08, 10).
- **Việc còn lại trước khi gắn tag `phase-2`** (ưu tiên theo mức ảnh hưởng tới test ẩn):
  1. Sửa fixture `test_lat2.py` (`random_fish: false`) để `main` xanh lại — mhoo40.
  2. Sửa tốc độ chéo trong `_reflect_1d` + thêm test bơi chéo — mhoo40.
  3. Áp I-1: `contract.py` nhận `burn_s` hữu hạn khi bật `burn`, manifest `"extensions": ["burn"]`, `burn_s: 20`, mục README — s0ra1n0 + nguyenhung1901.
  4. UI Phase 2 (menu, pause, màn chuyển Ngày, HUD, `live.py --mode day`) — tiepnnk01-10 + nguyenhung1901.
- **Bài học cho phase sau:** test xanh chưa đủ để kết luận AC đạt — tốc độ chéo của cá chỉ lộ ra khi đo trên một lần chạy thật; merge tính năng mới phải chạy lại toàn bộ test trước khi vào `main` (commit cá bơi vào thẳng `main` làm đỏ một test P1).
