# Kế hoạch Phase 1 (PRD-0, 0:00–1:00)

**Mục tiêu:** chơi được `gather` và `quan` đúng luật lõi PRD-0 (mục F), kho nối hai tiến trình theo mục G, smoke hai tiến trình xanh trên `main`, tag `phase-1` trước 1:00.

**Mốc:** 0–15 kickoff + chốt hợp đồng · 15–45 làm lát song song (phút 20 rà vướng, **phút 25 xuất file kho thật**) · 45–55 tích hợp, smoke, ma trận truy vết · 55–60 dự phòng, tag.

## Việc / người / phụ thuộc

| ID | Việc | AC | Người | Phụ thuộc | File chính |
|---|---|---|---|---|---|
| T0 | Chốt hợp đồng: schema kho + `inventory.sample.json`, danh sách event (tên, `data`, ai phát), giao diện sim↔UI (snapshot đọc được, lệnh `move/interact/catch`) | AC-P1-01 | HoangHongNgo | — (phút 0–15) | `docs/contracts/` |
| T1 | Lát 1: oxy theo `d` cuối bước (mặt nước +6, dưới nước −1, kẹp), `dive`/`surface`, `oxygen_empty`, đếm ngạt → `choke` (−1 Máu, 60 tick), Máu 0 → `faint` (`lost` LIFO) + `gather_end` `fainted` kho rỗng; giỏ LIFO, trần 12 | AC-P1-02, 03 | ChuTungDuongg | T0 | `chonoi/sim/gather.py` (bước 2) |
| T2 | Lát 2: hái nút ready gần nhất ở mặt nước (hòa theo id), `gather`/`hold_full`, `regrow_ticks`; `catch` dưới nước khi hết hồi: đàn gần nhất, `fish_caught` + cooldown, `hold_full` giữ đàn; bến xét trước; hết giờ giữ giỏ; ghi kho đúng một lần | AC-P1-04, 05, 06 | haiquanng | T0 (dùng chung `hold` với T1, thống nhất hàm thêm vào giỏ) | `chonoi/sim/gather.py` (bước 3–5) |
| T3 | Lát 3: khách fixture + suy `reserved`; lịch khách (`first_customer_tick`, mỗi 15 s, theo `phase_tick`), bàn trống id nhỏ nhất, chọn món đều theo seed trong món đủ kho khả dụng, `no_dish`; kiên nhẫn giảm, `customer_left` (patience −0.5 uy tín / closing); nhả giữ chỗ; kiểm mâu thuẫn scenario quán (mã 2) | AC-P1-07, 08, 10 | minhphuong150505 | T0, kho mẫu | `chonoi/sim/quan.py`, `chonoi/scenario.py` |
| T4 | Lát 4: chọn tối đa một interact (khoảng cách, bếp trước bàn, id); bếp idle lấy đơn reserved cũ nhất → `cook_started`; chín → `dish_ready`; bưng `dish_picked` (tay 1 món); phục vụ `served` + boa floor(giá×0.2) nếu kiên nhẫn ≥ 50%; ăn xong `paid`; hết ca trả/đuổi khách rồi `quan_end`; uy tín kẹp [0,5]; điểm | AC-P1-09, 10 | phuthaitran | T3 (cấu trúc khách/đơn) — làm trước bằng scenario dựng sẵn khách | `chonoi/sim/quan.py` |
| T5 | HUD trong `chonoi/web/index.html`: sáng (thời gian, oxy, Máu, giỏ), tối (kho khả dụng, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín); README: chạy từ clone sạch ≤ 3 lệnh, điều khiển, cách tính điểm, lệnh test | AC-P1-11, 12 | RachalHys | T0 (giao diện sim↔UI) | `chonoi/web/`, `README.md` |
| T6 | Test theo AC (mỗi lát ≥ 1 test hộp đen trong `tests/test_p1_*.py`), ma trận truy vết, lưu output thật vào `docs/proof/phase-1/` | tất cả | RachalHys (+ mỗi dev viết test lát mình) | T1–T4 | `tests/`, `docs/verification/phase-1.md` |
| T7 | `team`/`team_size`, kiểm dải hợp lệ tuning trong `contract.py`; gộp PR, smoke hai tiến trình trên `main`, gắn tag `phase-1` | AC-P1-01, 06 | HoangHongNgo | tất cả | `game.contract.json`, `chonoi/contract.py` |
| T8 | Ghi chép: mỗi người tự ghi `docs/ai-usage-log.md` (phần mình), `docs/members/<handle>.md`; PO giữ `docs/clarify.md`, Scrum giữ `docs/standup.md`, `docs/retro.md` | — | mọi người | — | `docs/` |

## Tiêu chí chấp nhận (AC)

- **AC-P1-01** `game.contract.json` đủ khóa Test Contract v1.0, `team_size` = 6; hợp đồng kho có schema + ví dụ hợp lệ.
- **AC-P1-02** Oxy/ngạt đúng mục F: chạm oxy 0 ở t, ở dưới liên tục → `choke` ở t+59; nổi lên đúng bước đó thì không ngạt.
- **AC-P1-03** Máu 0 → `faint` (`lost` LIFO) → `gather_end` `fainted`, file kho `{"items":{}}`.
- **AC-P1-04** Hái: chỉ ở mặt nước, nút đúng mép bán kính vẫn hái, `hold_full` không đổi nút, mọc lại sau 1200 tick.
- **AC-P1-05** Bắt cá: chỉ dưới nước, đủ yield (ca_linh 3, ca_loc 1), cooldown 30 tick, `hold_full` giữ đàn.
- **AC-P1-06** Smoke hai tiến trình (dock.json + dock-inputs.json, seed 42) → quán tick 0 có `stock:{"bong_sung":2,"ca_loc":1}`; chạm `--ticks` trước khi kết thúc thì không ghi kho.
- **AC-P1-07** Khách đầu ở `phase_tick` 120, sau đó mỗi 900 tick; giữ đúng công thức; `no_dish` khi thiếu món; cùng seed → giống từng byte.
- **AC-P1-08** Hết kiên nhẫn → `customer_left` patience, uy tín −0.5, nhả giữ chỗ.
- **AC-P1-09** Nấu → bưng → phục vụ → ăn 600 tick → `paid` với boa đúng; tiền, `earned`, uy tín, điểm đúng.
- **AC-P1-10** Hết ca: khách đang ăn trả `closing`, khách chờ rời không trừ uy tín, rồi `quan_end`.
- **AC-P1-11** HUD hiển thị đủ các trường mục 2 của PRD-0 khi chơi bằng `chonoi.live`.
- **AC-P1-12** README: chạy từ clone sạch ≤ 3 lệnh, điều khiển, cách tính điểm, test 1 lệnh.

## Rủi ro

- T1 và T2 cùng sửa `gather.py`: chia theo bước trong `step()` và chốt hàm thêm vào giỏ ngay phút 15 để tránh xung đột.
- T3 và T4 cùng sửa `quan.py`: T3 viết cấu trúc khách/đơn trước phút 25; T4 dựng khách bằng scenario để không chờ.
- Lịch khách, chọn món theo seed, thứ tự xử lý cuối ca dễ sai lệch từng tick: hỏi Anh Năm sớm, ghi vào `docs/clarify.md`.
- Windows: `python3` chỉ có trong Git Bash; cổng 8000 có thể bị chặn (dùng `--port 8765`) và cần `PYTHONUTF8=1` khi chạy `chonoi.live`.
- Nhóm 6 người phải làm ≥ 2 mục mở rộng trong cả buổi lab: chưa làm ở Phase 1, để từ Phase 2 khi lõi xong.
