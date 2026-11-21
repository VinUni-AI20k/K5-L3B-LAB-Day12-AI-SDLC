# Ma trận truy vết Phase 2 (Contract v1.1)

| AC / Hạng mục | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| **AC-P2-01** (`contract_version: "1.1"`, số liệu chuẩn 6 nguyên liệu, 6 món, N1–N6, B1–B2, T1–T4, `day_plan` D1–D5, `shop`) | `python3 .agents/skills/verify-contract/verify.py` & `tests/test_gather_p2.py`, `tests/test_quan_p2_kitchen.py` | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-02** (Cá bơi 1.5 m/s, phản xạ mép, đổi hướng mỗi 120 tick, sinh cá `360·k`, trần 12, `random_fish: false`) | `tests/test_gather_p2.py::GatherP2Fish` | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-03** (Cá Sấu Năm Chèo M1/M2: `patrol`/`chase`/`recoil`, chạm `-1` Máu, rơi LIFO `floor(hold/2)`, bất tử 90 tick, `faint`) | `tests/test_gather_p2.py::GatherP2Monsters` | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-04** (Quán v1.1: 2 bếp B1–B2, 4 bàn T1–T4, 6 món, lọc menu theo `day_plan`) | `tests/test_quan_p2_kitchen.py` (10 test), `tests/test_day.py` | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-05** (`--mode day`, vòng `gather → quan → shop`, `--days 1..5`, nâng cấp `oxygen`/`hp` hiệu lực từ Ngày kế, `pause`, mã `2`) | `tests/test_day.py` (19 test), `tests/test_pause_inputs.py` (8 test), smoke 1 Ngày & 2 Ngày | [tv3-day/README.md](../proof/phase-2/tv3-day/README.md) · [day1-noinput.jsonl](../proof/phase-2/tv3-day/day1-noinput.jsonl) · [day2-upgrade.jsonl](../proof/phase-2/tv3-day/day2-upgrade.jsonl) | **Đạt** |
| **AC-P2-06** (Mở rộng `burn` — Cháy món `burn_s: 20`, khai `extensions: ["burn"]`) | `tests/test_quan_burn.py` (10 test) | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-07** (Hiệu năng headless ≤ 20 s/Ngày & tính tất định từng byte) | 1 Ngày 22.200 tick chạy 0,93 s; 2 lần chạy giống từng byte | [tv3-day/README.md](../proof/phase-2/tv3-day/README.md) | **Đạt** |
| **AC-P2-08** (Regression P1 với số chuẩn v1.1; test đổi có ghi lý do) | `test_smoke_p1`, `test_gather_p1`, `test_quan_lat3`, `test_quan_kitchen`, `test_quan_service`, `test_qa_regression_p1` | [test-suite.txt](../proof/phase-2/test-suite.txt) | **Đạt** |
| **AC-P2-09** (UI Menu chính, Pause `Esc`/`P`, HUD vòng ngày & Cá Sấu trên `chonoi.live`) | TV4 đang làm song song trong Pod Phase 4 (`chonoi/web/index.html`) | *(chưa gộp ở tag `phase-2`)* | **Chưa đạt** *(sẽ bổ sung ở bản cập nhật UI tiếp theo)* |

## Lý do cập nhật test cũ (theo DoD Phase 2)
- `tests/test_smoke_p1.py`: đổi kiểm số cá đầu ca sang đọc `fish_initial` (v1.1 là 8 đàn); bỏ `"day"` khỏi danh sách mode bị từ chối vì v1.1 hỗ trợ `--mode day`.
- `tests/test_gather_p1.py`: thêm `random_fish: false` vào `test_catch_fish_yield_cooldown_and_tie_break` vì ở v1.1 cá tự bơi khi `random_fish=true`.
- `tests/test_quan_lat3.py` & `tests/test_quan_kitchen.py`: cập nhật theo bố cục 4 bàn (`T1`–`T4`) và 2 bếp (`B1`–`B2`) của v1.1.

## Đánh giá ngắn
- **Đạt:** Toàn bộ lõi v1.1 (`gather`, `monsters`, `quan`, `day`, `shop`, `pause`, `scenario` khối `day`), mở rộng `burn`, regression P1 và tính tất định từng byte đều đạt 100%.
- **Chưa đạt:** Phần giao diện Menu/Pause/HUD vòng ngày của TV4 chưa kịp merge trước mốc tag `phase-2` (ghi nhận trung thực, đang triển khai song song).
- **Điều cần chỉnh cho Phase 3:** Chốt trước patch giao tiếp `scenario.py` và `game.contract.json` ngay đầu phase để TV2 (`v1.2` độ tươi) không bị chờ merge.
