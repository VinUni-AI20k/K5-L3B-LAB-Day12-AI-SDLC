# Ma trận truy vết Phase 2

Cập nhật 2026-11-21 trên `main` sau PR #31 (gồm P2-02, P2-03, P2-04, P2-05, P2-06, P2-07, P2-09, P2-10). Nguồn yêu cầu: Ticket-02 (khóa theo giờ, nhóm không đọc được bản gốc; luật dựng từ `game.contract.json` v1.1 và ghi mọi chỗ đoán ở `docs/clarify.md`). Mã AC theo `docs/plan/phase-2.md`.
Chạy lại toàn bộ: `PYTHONPATH=tests:. python -m unittest discover -s tests` (250 test), `python tools/smoke_phase1.py` (27 mục), `python tools/smoke_phase2.py` (15 mục), `python tools/check_determinism.py` (gather, quan, day), `python tools/check_no_hardcode.py`. Kết quả ở [p2-09-smoke.md](../proof/phase-2/p2-09-smoke.md) và [p2-10-regression.md](../proof/phase-2/p2-10-regression.md).
Cột kết quả ghi trung thực: **đạt**, **đạt một phần** hoặc **chưa đạt**.

## A. Luật chơi v1.1

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 Contract 1.1 với số chuẩn mới (mục 1.1, 1.3), sửa test Phase 1 lệch số có lý do | Test khóa khóa/giá trị contract; hồi quy Phase 1 | `tests/test_contract_v11.py` (21 test), PR #23, [p2-10-regression.md](../proof/phase-2/p2-10-regression.md) | Đạt |
| AC-P2-02 Cá bơi, phản xạ, sinh theo seed, `fish_spawned`, `age_ticks` | Test luật; smoke có `fish_spawned` trong ca gather | `tests/test_p2_fish.py` (7 test), `tools/smoke_phase2.py`, [p2-03-fish.md](../proof/phase-2/p2-03-fish.md) | Đạt (đàn đầu 8 con theo giả định ở `clarify` #8, chờ PO) |
| AC-P2-03 Cá Sấu tuần tra, đuổi, cắn (Máu, mất giỏ, bất tử, lùi), ngất do quái; Ngày 3 thêm M2 | Test luật; phá thử `monsters.py` | `tests/test_p2_monsters.py` (17 test), PR #30 (7 cách phá thử: cả 7 bị bắt sau khi thêm test mặt nước) | Đạt một phần: `recoil_dist`, làm tròn mất giỏ, điều kiện đuổi là giả định chờ PO (`clarify` #7, #11, #12) |
| AC-P2-04 Quán 2 bếp, 4 bàn, 6 món; lọc món theo kế hoạch Ngày; nhận tiền, uy tín, kho từ Ngày trước | Test luật; smoke tick 0 và ca đủ | `tests/test_p2_quan.py` (10 test), `tools/smoke_phase2.py` | Đạt |
| AC-P2-05 Shop nâng cấp oxy và Máu: giá, cấp, `bought`, `buy_failed` (`funds`, `max_level`, `unknown`), `shop_end` | Test luật | `tests/test_p2_shop.py` (5 test), [p2-06-shop.md](../proof/phase-2/p2-06-shop.md) | Đạt |

## B. Chế độ `day`, pause, input mới

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-06 `--mode day --days 1..5`: gather → quán → shop, kế hoạch D1–D5, thứ tự chuyển pha (mục 4.5), tiền/uy tín/nâng cấp giữ xuyên Ngày (nâng cấp có hiệu lực từ Ngày sau), `days_complete` | Test trong tiến trình và hộp đen; smoke 2 Ngày; phá thử 10 cách | `tests/test_p2_day.py` (28 test), `tools/smoke_phase2.py` (mục day), PR #28 (10 cách phá thử: cả 10 bị bắt, một cách ban đầu sống sót rồi đã thêm test) | Đạt |
| `pause` (cả ba chế độ), `shop_done`, `buy` (chỉ ở frame khai báo), mã 2 cho `--days` ngoài 1..5 và `--inventory` với day | Test và smoke hộp đen | `tests/test_p2_day.py`, `tools/smoke_phase2.py` | Đạt |
| Tất định của `day` | `check_determinism.py` chạy 2 Ngày đủ, so từng byte | `tools/check_determinism.py`, smoke "day: tất định" | Đạt |
| AC-P2-07 Menu, pause, HUD trên cửa sổ chơi (`chonoi.live` chế độ day) | Chưa có trên `main` (P2-08 của C) | nhánh `c/p2-08-menu-pause-hud` chưa gộp | **Chưa đạt** |

## C. Hợp đồng và hồi quy

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-08 Smoke tích hợp phút 20: gather `--inventory-out` → quan `--inventory`, luật v1.1 | Smoke hộp đen | [p2-09-smoke.md](../proof/phase-2/p2-09-smoke.md) | Đạt |
| AC-P2-09 Hồi quy Phase 1: các test và smoke Phase 1 còn đạt | 250 test, smoke Phase 1 27/27 | [p2-10-regression.md](../proof/phase-2/p2-10-regression.md) | Đạt |
| `docs/contracts/README.md` khớp code v1.1 (sự kiện mới, snapshot `day`, input mới) | Đọc đối chiếu code | PR của P2-11 (chỉ thêm, báo cả nhóm trong mô tả PR) | Đạt (sau khi PR này được gộp) |

### Test Phase 1 phải đổi và lý do
- Số "một bàn" thành "bốn bàn" và các số chuẩn mới của contract v1.1: sửa ở PR #23 (lý do trong commit).
- `--mode day bị từ chối ở v1.0` trong `tools/smoke_phase1.py` và `tests/test_smoke_p1.py`: day nay hợp lệ, đổi thành "`--days` với gather → mã 2" (PR #28).
- `invuln_ticks` trong `tests/test_gather_prd.py`: v1.0 từ chối, v1.1 chấp nhận; kiểm theo `contract_version` (PR #30).

## D. Nhóm và quy trình

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Mỗi người ≥ 3 commit bằng tài khoản của mình | Đếm commit trên `main` | D: 65 (`luongvh2510` 31 và `luongvh` 34, cùng email); A (`NguyenDucNhat3006`): 7; B (`HoAnhTu245`): 6; C (`Cuongngucuteee`): 3; còn 9 commit của `Hai Duong` chưa biết thuộc ai | Đạt một phần: B vẫn dùng `HoAnhTu245` trong khi `TEAM.md` ghi `TuHoAnh`, cần xác nhận tài khoản |
| Nhật ký AI, hồ sơ cá nhân, standup | Kiểm file | `docs/ai-usage-log.md` có dòng của B và D; `docs/members/` chỉ có hồ sơ của B (tên file chưa theo `<handle>.md`) và D | **Chưa đạt** với A và C |
| `docs/retro.md` mục Phase 2 | Đọc file | Còn trống (việc P2-12) | **Chưa đạt** |
| Tag `phase-2` | `git tag`, chạy test tại tag | Chưa gắn (việc P2-13, chờ P2-08 và retro) | **Chưa đạt** |

## Đánh giá ngắn

- **Đạt:** luật gather v1.1 (cá, Cá Sấu), quán v1.1, Shop, chế độ `day` với pause và input mới, hợp đồng tài liệu khớp code, tất định, hồi quy Phase 1. 250 test xanh, smoke 27/27 và 15/15.
- **Đạt một phần:** Cá Sấu (giả định chờ PO), commit theo người (B, tài khoản).
- **Chưa đạt:** menu, pause, HUD trên cửa sổ chơi (P2-08), nhật ký AI và hồ sơ của A và C, retro Phase 2, tag `phase-2`.
- **Hạn chế:** Ticket-02 không đọc được nên mức "đạt" là theo contract v1.1 và hiểu biết của nhóm, chưa có bộ test ẩn của giảng viên. Smoke hộp đen chưa phủ `buy` ở Shop (chỉ có unit test) và `chonoi.live` ở chế độ day.
- **Phải xong trước khi gắn `phase-2`:** gộp P2-08, retro (P2-12), bổ sung ghi chép của A và C, cập nhật bảng này sau khi gộp rồi chạy lại toàn bộ lệnh ở đầu file tại đúng commit gắn tag.
