# Ma trận truy vết Phase 2

Cập nhật 2026-11-21 trên `main` tại commit `db49e35` (sau PR #34; gồm P2-02 đến P2-12). Đã chạy lại toàn bộ lệnh dưới đây tại commit này; commit gắn tag chỉ khác commit này ở tài liệu. Nguồn yêu cầu: Ticket-02 (khóa theo giờ, nhóm không đọc được bản gốc; luật dựng từ `game.contract.json` v1.1 và ghi mọi chỗ đoán ở `docs/clarify.md`). Mã AC theo `docs/plan/phase-2.md`.
Chạy lại toàn bộ: `PYTHONPATH=tests:. python -m unittest discover -s tests` (259 test), `python tools/smoke_phase1.py` (27 mục), `python tools/smoke_phase2.py` (15 mục), `python tools/check_determinism.py` (gather, quan, day), `python tools/check_no_hardcode.py`. Kết quả ở [p2-09-smoke.md](../proof/phase-2/p2-09-smoke.md) và [p2-10-regression.md](../proof/phase-2/p2-10-regression.md), [p2-08-ui.md](../proof/phase-2/p2-08-ui.md).
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
| AC-P2-07 Menu chính, pause, HUD, Shop trên cửa sổ chơi (`chonoi.live` chế độ day) | Test API và phím; ảnh chụp trình duyệt thật; D tự bấm phím thật cho menu, pause, mua đồ ở Shop (1, 2) | `tests/test_p2_live_ui.py`, [p2-08-ui.md](../proof/phase-2/p2-08-ui.md) và 3 ảnh, PR #35 | Đạt một phần: chưa ai chơi tay trọn một Ngày (Lặn → Quán → Shop) bằng bàn phím; bố cục và phím do nhóm chọn vì không đọc được đề mục 2 |

## C. Hợp đồng và hồi quy

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-08 Smoke tích hợp phút 20: gather `--inventory-out` → quan `--inventory`, luật v1.1 | Smoke hộp đen | [p2-09-smoke.md](../proof/phase-2/p2-09-smoke.md) | Đạt |
| AC-P2-09 Hồi quy Phase 1: các test và smoke Phase 1 còn đạt | 250 test, smoke Phase 1 27/27 | [p2-10-regression.md](../proof/phase-2/p2-10-regression.md) | Đạt |
| `docs/contracts/README.md` khớp code v1.1 (sự kiện mới, snapshot `day`, input mới) | Đọc đối chiếu code | PR #32 và #35 (chỉ thêm, đã báo cả nhóm trong mô tả PR) | Đạt |

### Test Phase 1 phải đổi và lý do
- Số "một bàn" thành "bốn bàn" và các số chuẩn mới của contract v1.1: sửa ở PR #23 (lý do trong commit).
- `--mode day bị từ chối ở v1.0` trong `tools/smoke_phase1.py` và `tests/test_smoke_p1.py`: day nay hợp lệ, đổi thành "`--days` với gather → mã 2" (PR #28).
- `invuln_ticks` trong `tests/test_gather_prd.py`: v1.0 từ chối, v1.1 chấp nhận; kiểm theo `contract_version` (PR #30).

## D. Nhóm và quy trình

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Mỗi người ≥ 3 commit bằng tài khoản của mình | Đếm commit trên `main` | D: 72 (`luongvh2510` 35 và `luongvh` 37, cùng email); A (`NguyenDucNhat3006`): 7; B (`HoAnhTu245`): 7; C (`Cuongngucuteee`): 7; còn 9 commit của `Hai Duong` chưa biết thuộc ai | Đạt một phần (mỗi người ≥ 3 commit): B vẫn dùng `HoAnhTu245` trong khi `TEAM.md` ghi `TuHoAnh`, cần xác nhận tài khoản |
| Nhật ký AI, hồ sơ cá nhân, standup | Kiểm file | `docs/ai-usage-log.md` có dòng của B và D; `docs/members/` chỉ có hồ sơ của B (tên file chưa theo `<handle>.md`) và D | **Chưa đạt** với A và C |
| `docs/retro.md` mục Phase 2 | Đọc file | Đã điền: bản của D (PR #33) và phần của TuHoAnh (PR #34); chưa có phần của A và C | Đạt một phần |
| Tag `phase-2` | `git tag`, chạy test tại tag | Chưa gắn (việc P2-13, cần người dùng đồng ý trước khi đẩy tag) | **Chưa đạt** |

## Đánh giá ngắn

- **Đạt:** luật gather v1.1 (cá, Cá Sấu), quán v1.1, Shop, chế độ `day` với pause và input mới, giao diện chơi có menu, pause, HUD, Shop, hợp đồng tài liệu khớp code, tất định, hồi quy Phase 1. 259 test xanh, smoke 27/27 và 15/15.
- **Đạt một phần:** Cá Sấu (giả định chờ PO), giao diện chơi (chưa chơi tay trọn một Ngày), commit theo người (B dùng tài khoản khác `TEAM.md`), retro (thiếu phần của A và C).
- **Chưa đạt:** nhật ký AI và hồ sơ cá nhân của A và C, `standup.md` còn trống, tag `phase-2`.
- **Hạn chế:** Ticket-02 không đọc được nên mức "đạt" là theo contract v1.1 và hiểu biết của nhóm, chưa có bộ test ẩn của giảng viên. Smoke hộp đen chưa phủ `buy` ở Shop (chỉ có unit test và lần bấm thử của D); câu hỏi `clarify` #6 đến #12 chờ PO.
- **Trước khi gắn `phase-2`:** nếu A và C kịp nộp ghi chép thì cập nhật hai dòng "Chưa đạt" ở trên; chạy lại lệnh đầu file tại đúng commit gắn tag nếu có thay đổi code, rồi mới gắn tag (cần người dùng đồng ý).
