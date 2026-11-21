# Ma trận truy vết Phase 1

**Nguồn:** PRD-0 (`docs/prd/phase-1.md`).
**Bằng chứng tổng:** chạy `python .agents/skills/verify-phase/verify.py --phase 1` trên commit `7d85efa` (main sau khi merge lát 1, 2, 3), xem [`docs/proof/phase-1/summary.md`](../proof/phase-1/summary.md).
**Kết quả chạy:** 58 test, OK (2 skipped); tất định đạt; kho gather → quán đạt; `check_team` đạt.
**Mã AC:** nhóm tự đặt `AC-P1-xx` theo các mục của PRD-0, vì PRD không có mã AC.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 Headless đúng CLI, mã thoát 0/1/2, lỗi đầu vào thoát **trước** khi ghi (mục B, C) | `test_smoke_p1.Contract.test_con_01/03*`, `ScenarioModes.*`, `test_scenario_out_of_domain_exit_2` | [tests.txt](../proof/phase-1/tests.txt) | đạt |
| AC-P1-02 Cùng seed → JSONL giống từng byte (mục E) | `test_con_02_deterministic_bytes`, `test_gather_lat1...test_tat_dinh_tung_byte`; verify chạy gather + quán 2 lần, 600 tick | [determinism.txt](../proof/phase-1/determinism.txt) | đạt |
| AC-P1-03 Bơi: ramp ≤ 6 tick, 4 m/s, chặn mép, `d` không âm, hướng 90° = xuống (mục F chung) | `test_smoke_p1.Movement.*` | [tests.txt](../proof/phase-1/tests.txt) | đạt |
| AC-P1-04 Oxy theo `d` cuối bước: dưới nước −1, mặt nước +6 kẹp tối đa, `oxygen_empty` một lần | `test_gather_lat1.Oxygen.*` | [lat1.md](../proof/phase-1/lat1.md) | đạt |
| AC-P1-05 Ngạt: chạm 0 ở t → `choke` ở t+59, mỗi 60 tick −1 Máu; nổi lên kịp thì không ngạt | `test_gather_lat1.Choke.*` | [lat1.md](../proof/phase-1/lat1.md) | đạt |
| AC-P1-06 Ngất: bỏ giỏ LIFO, `faint` → `gather_end fainted`, kho `{"items":{}}`; ngất thắng hết giờ cùng tick | `test_gather_lat1.Faint.*` | [lat1.md](../proof/phase-1/lat1.md) | đạt |
| AC-P1-07 `dive` / `surface` chỉ khi đổi phía, `pos` sau di chuyển | `test_gather_lat1.DiveSurface.*` | [lat1.md](../proof/phase-1/lat1.md) | đạt |
| AC-P1-08 Hái nút ở mặt nước (gần nhất, hòa theo id), `regrow`, `hold_full` (mục F bước 4) | Chỉ đọc code `GatherSim._try_gather` (lát 2), đối chiếu PRD | — | **chưa kiểm chứng**: lát 2 chưa có test |
| AC-P1-09 Bắt cá dưới nước, lấy toàn bộ yield, hồi 30 tick, thiếu chỗ → `hold_full` giữ đàn (mục F bước 5) | Chỉ đọc code `GatherSim._try_catch` (lát 2) | — | **chưa kiểm chứng**: lát 2 chưa có test |
| AC-P1-10 Cập bến hoặc hết giờ giữ giỏ, ghi kho đúng một lần; chạm `--ticks` trước thì không ghi (mục G) | `test_time_ends_gather_and_keeps_hold`, `Integration.test_inv_01_*` | [tests.txt](../proof/phase-1/tests.txt) | đạt |
| AC-P1-11 Kho gather → quán: quán tick 0 có đúng `stock`; schema sai → mã 2 (mục G) | `Integration.*`; verify bước kho | [inventory.txt](../proof/phase-1/inventory.txt) | đạt |
| AC-P1-12 Khách đến theo lịch, chọn món đủ nguyên liệu, giữ chỗ, `no_dish`, hết bàn bỏ lượt (mục F quán bước 5) | `test_quan_lat3.Arrival.*` | [tests.txt](../proof/phase-1/tests.txt) | đạt; 1 test cần ≥ 2 bàn đang skip (preset P1 chỉ có T1) |
| AC-P1-13 Kiên nhẫn, khách rời `patience` (−0.5 uy tín) hoặc `closing` (không trừ), kẹp uy tín | `test_quan_lat3.Leaving.*` | [tests.txt](../proof/phase-1/tests.txt) | đạt |
| AC-P1-14 Khách dựng từ scenario, suy ra giữ chỗ, fixture mâu thuẫn → mã 2 | `test_quan_lat3.ScenarioCustomers.*` | [tests.txt](../proof/phase-1/tests.txt) | đạt một phần (1 test skip vì cần ≥ 2 bàn); còn TODO kiểm mâu thuẫn trong `scenario.py` |
| AC-P1-15 Bếp, bưng, phục vụ, trả tiền, boa, uy tín (`cook_started` … `paid`) | — | — | **chưa đạt**: lát 4 chưa làm (`_tick_stoves_and_eating`, `_interact`, `_pay` còn TODO) |
| AC-P1-16 Chơi được cả hai buổi, HUD đọc được (DoD 1) | Chơi thử `chonoi.live` | — | **chưa đạt**: buổi tối chưa nấu và phục vụ được (phụ thuộc AC-P1-15) |
| AC-P1-17 `TEAM.md` đủ 5 người, `team_size` = 5, handle hợp lệ | `tools/check_team.py` | [team.txt](../proof/phase-1/team.txt) | đạt; mục "Kênh liên lạc" trong thỏa thuận còn trống |
| AC-P1-18 Hợp đồng kho có schema + ví dụ; giao diện sim↔UI; danh sách sự kiện | Đọc lại `docs/contracts/README.md` | [contracts](../contracts/README.md) | đạt |
| AC-P1-19 README: chạy từ clone sạch ≤ 3 lệnh, điều khiển, cách tính điểm, test 1 lệnh | Đọc `README.md`, mục "Nhóm ChoNoiCaMau" | [README](../../README.md) | đạt (chưa thử clone sạch trên macOS/Linux) |
| AC-P1-20 Tag `phase-1` trên `main` chậm nhất 1:00 | `git tag` | — | **trễ hạn**: gắn sau 1:00, ghi trung thực |

## Đánh giá ngắn
- **Đạt:** Test Contract v1.0 (CLI, mã thoát, tất định, file kho), toàn bộ buổi sáng (bơi, oxy, ngạt, ngất, cập bến), và phần khách của quán (lát 3).
- **Chưa đạt / chưa kiểm chứng:**
  - Quán lát 4 (bếp, phục vụ, tiền, boa), nên chưa chơi trọn hai buổi.
  - Lát 2 (hái, bắt cá) có code nhưng chưa có test.
  - Kiểm mâu thuẫn scenario quán còn TODO.
  - Tag `phase-1` trễ hạn.
- **Cần chỉnh cho phase sau:**
  - Viết test hộp đen cùng lúc với code, không để dồn về cuối.
  - Chốt `docs/contracts/` ngay trong 15 phút đầu.
  - Hoàn tất lát 4 và test lát 2 như nợ Phase 1, trước khi lên v1.1.
  - Integrator chạy `verify-phase` trước mỗi lần gắn tag.
