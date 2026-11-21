# Ma trận truy vết Phase 1

| AC | Module | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| AC-P1-CON-01: Headless CLI (`--mode gather\|quan`, `--ticks 0`, dòng `end` cuối) | M6 | `unittest` (`test_smoke_p1.Contract`) | *Chạy ở `M6.4` tại commit gắn tag* | Đạt (đã qua smoke) |
| AC-P1-CON-02: Tất định byte-for-byte (cùng seed → JSONL & file kho giống từng byte) | M6 | `unittest` (`test_integration_m6.py`) + so khớp hash ở `M6.4` | *Chờ lưu `docs/proof/phase-1/determinism.txt`* | Đạt (khung + `test_integration_m6`) |
| AC-P1-CON-03: Đầu vào / scenario mâu thuẫn thoát mã `2` trước khi ghi output | M6 | `unittest` (`test_smoke_p1.py`, `test_scenario_m6.py`) | *Chờ lưu `docs/proof/phase-1/tests.log`* | Đạt (38+ tests OK) |
| AC-P1-INV-01: Tích hợp 2 tiến trình `gather --inventory-out` → `quan --inventory` | M2 / M6 | `unittest` (`test_smoke_p1.Integration`, `test_integration_m6.py`) | *Chờ lưu `docs/proof/phase-1/integration.log`* | Đạt (khung + smoke 2 tiến trình) |
| AC-P1-M1-01: Bơi, tăng/giảm tốc (`ramp_max_ticks`), chặn biên `[0,100]×[0,30]`, `dive`/`surface` | M1 | Unit test M1 (`M1.2`, `M1.4`) | *Chờ M1 nộp bằng chứng Đợt 4* | Chờ bàn giao M1 |
| AC-P1-M1-02: Oxy (dưới nước -1, mặt nước +6), `oxygen_empty`, ngạt (`choke`), ngất (`faint` mất giỏ LIFO + kho rỗng) | M1 | Unit test M1 (`M1.2`, `M1.4`) | *Chờ M1 nộp bằng chứng Đợt 4* | Chờ bàn giao M1 |
| AC-P1-M2-01: Hái nút ở mặt nước (`gather`, `node_regrown`, `hold_full`), bắt cá (`catch`, `fish_caught`, cooldown) | M2 | Unit test M2 (`M2.2`, `M2.4`) | [m2.md](../proof/phase-1/m2.md), [test_gather_m2.py](../../tests/test_gather_m2.py) | Đạt (10/10 AC pass) |
| AC-P1-M2-02: Giỏ LIFO (`hold_capacity`), cập bến (`docked`), hết giờ (`time`), xuất kho khớp `inventory.sample.json` | M2 | Unit test M2 (`M2.2`, `M2.4`) | [m2.md](../proof/phase-1/m2.md), [m2_catch.json](../proof/phase-1/m2_catch.json) | Đạt (khớp từng byte) |
| AC-P1-M3-01: Khách đến theo lịch (`customer_arrived`, `no_dish`), giữ chỗ nguyên liệu (`reserved`), kiên nhẫn, rời đi (`customer_left`) | M3 | Unit test M3 (`M3.2`, `M3.4`) | *Chờ M3 nộp bằng chứng Đợt 4* | Chờ bàn giao M3 |
| AC-P1-M4-01: `interact` bếp/bàn (`cook_started`, `dish_ready`, `dish_picked`, `served`), trả tiền (`paid`), boa, uy tín, `quan_end` | M4 | Unit test M4 (`M4.2`, `M4.4`) | *Chờ M4 nộp bằng chứng Đợt 4* | Chờ bàn giao M4 |
| AC-P1-M5-01: Chơi thử được cả 2 buổi trên `chonoi.live`, HUD đọc được các chỉ số tối thiểu | M5 | Chạy `python3 -m chonoi.live --mode gather\|quan`, chụp màn hình | *Chờ M5 nộp ảnh Đợt 4* | Chờ bàn giao M5 |
| AC-P1-TEAM-01: `TEAM.md` đủ 6 thành viên, `team_size: 6`, `check_team.py` xanh, hợp đồng kho trong `docs/contracts/` | M6 | `python tools/check_team.py` | `TEAM.md`, `docs/contracts/README.md` | Đạt |

## Đánh giá ngắn (cập nhật hoàn chỉnh ở `M6.5` trước khi gắn tag `phase-1`)
- Yêu cầu nào đạt / chưa đạt: *(PO cập nhật sau khi nhận bằng chứng M1–M5 ở Đợt 4)*
- Điều cần chỉnh cho phase sau: *(PO cập nhật trước khi chuyển sang Phase 2)*
