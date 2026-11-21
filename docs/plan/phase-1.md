# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** chơi được `gather` và `quan` đúng lõi PRD-0, qua Test Contract v1.0; smoke 2 tiến trình dock → quán xanh trên `main`; tag `phase-1` trước 1:00. Nhóm 3 người → không bắt buộc mở rộng.

## Việc / người / phụ thuộc

| # | Việc (AC) | File | Người | Phụ thuộc |
|---|---|---|---|---|
| 1 | So `game.contract.json` với preset mục A (chỉ kiểm, không sửa) | `game.contract.json` | Khuê | — |
| 2 | Hợp đồng: schema kho G + ví dụ, bảng sự kiện E, giao diện sim↔UI | `docs/contracts/` | Khuê | — (xong trước phút 15) |
| 3 | Hỏi Anh Năm các chỗ mơ hồ, ghi lại | `docs/clarify.md` | Khánh | — |
| 4 | Lát 1: bơi, oxy, ngạt (t+59), Máu, ngất (LIFO), dive/surface, giỏ | `chonoi/sim/gather.py` | Phong | 2 |
| 5 | Lát 2: cập bến (xét trước), hái, bắt cá, hold_full, cooldown, ghi kho | `chonoi/sim/gather.py` | Phong | 4 |
| 6 | Lát 3: lịch khách, chọn món theo seed, giữ chỗ, kiên nhẫn, `no_dish`, `customer_left` | `chonoi/sim/quan.py` | Khánh | 2 (dùng kho mẫu) |
| 7 | Lát 4: interact (khoảng cách → bếp trước bàn → id), nấu, bưng, `served`/`paid`, boa, uy tín, closing, `quan_end` | `chonoi/sim/quan.py` | Khánh (+ Khuê hỗ trợ) | 6 |
| 8 | Kiểm mâu thuẫn scenario mục D → mã 2 | `chonoi/scenario.py` | Khuê | 2 |
| 9 | Unit test case biên (ngạt t+59, nổi lên đúng tick ngạt, E đúng mép bến bước cuối, boa) | `tests/` | Khuê | 4–7 |
| 10 | README: chạy từ clone sạch ≤ 3 lệnh, điều khiển, điểm, lệnh test; chơi thử HUD | `README.md` | Phong | 5 |
| 11 | Chạy test + smoke dock → quán, lưu output; ma trận AC → bằng chứng | `docs/proof/phase-1/`, `docs/verification/phase-1.md` | Khuê | 4–10 |
| 12 | Ghi chép: `ai-usage-log`, `standup`, `members/<handle>.md` | `docs/` | cả nhóm | — |
| 13 | Merge `main`, tag `phase-1` | — | Khuê (Integrator) | 11 |

## Lịch (phút trong phase)

| Phút | Phong | Khánh | Khuê |
|---|---|---|---|
| 0–15 | đọc mục F (Gather) | hỏi Anh Năm, ghi `clarify.md` | chốt `docs/contracts/` |
| 15–25 | lát 1 | lát 3 | `scenario.py` |
| 25 | **xuất được file kho thật** | test quán bằng kho mẫu | chạy thử dock → quán |
| 25–45 | lát 2 | lát 4 | test case biên + hỗ trợ lát 4 |
| ~20–25 | standup 2–3 phút (đã xong / sắp làm / vướng) | | |
| 45–55 | README | merge vào `main` | test + smoke, proof, ma trận |
| 55–60 | dự phòng | | tag `phase-1` |

Quy trình: nhánh `<handle>/<việc>` → PR vào `main`, người dự phòng review, chạy test trước khi gộp. Mỗi người ≥ 3 commit có nội dung.

## Rủi ro
- Thứ tự event trong một tick phải khớp chính xác (test ẩn so từng byte) → test bám mục F.
- `quan` nặng nhất (lát 3 + 4 cùng một người) → Khuê hỗ trợ lát 4 sau khi xong contracts.
- Chỗ PRD mơ hồ (`unfulfillable`, `random_fish`, stream RNG chọn món, tỷ lệ kiên nhẫn khi boa) → chốt qua `docs/clarify.md`.
- Nhóm 3 người (đề yêu cầu 4–6): chờ giảng viên xác nhận, xem `docs/clarify.md` #1.
- Windows thiếu `python3` → dùng shim trong `.venv` (xem `AGENTS.md`).
