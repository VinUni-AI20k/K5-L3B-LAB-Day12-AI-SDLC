# Kế hoạch Phase 1 — PRD-0 (0:00–1:00)

**Mục tiêu:** chơi được `gather` và `quan`, nối nhau qua file kho; headless đúng Test Contract v1.0; tag `phase-1` trên `main` trước 1:00.

## Việc / người / phụ thuộc

| # | Việc | Người | File chính | Phụ thuộc | AC |
|---|---|---|---|---|---|
| 0 | Chốt hợp đồng kho (mục G), danh sách sự kiện (mục E), giao diện sim ↔ UI | NgChiVinh | `docs/contracts/` | — (xong trước phút 15) | AC-P1-01 |
| 1 | Lát 1: dive/surface, oxy, oxygen_empty, ngạt/choke, Máu, faint (bỏ giỏ LIFO, kho rỗng) | NgChiVinh | `chonoi/sim/gather.py` (bước 2) | 0 | AC-P1-02 |
| 2 | Lát 2: hái nút (gather, hold_full, regrow), bắt cá (fish_caught, cooldown), cập bến, kho | TrungHieuPh | `chonoi/sim/gather.py` (bước 3–4) | 0; thử xuất kho thật trước phút 25 | AC-P1-03, AC-P1-04 |
| 3 | Lát 3: khách theo lịch, chọn món theo seed, giữ chỗ; cung cấp `_available()` / `_remove_customer()` cho lát 4; kiên nhẫn, no_dish, customer_left; kiểm scenario quán → mã 2 | 22520160 | `chonoi/sim/quan.py`, `chonoi/scenario.py` | 0; dùng `inventory.sample.json`; chốt schema khách với lát 4 | AC-P1-05 |
| 4 | Lát 4: interact bếp/bàn (cook_started, dish_ready, dish_picked, served), ăn, paid, boa, uy tín, đóng ca, quan_end | HoangQuan23112004 | `chonoi/sim/quan.py` | 3 (cấu trúc khách theo mục D — chốt cùng lát 3 ngay đầu) | AC-P1-06 |
| 5 | HUD: gather (thời gian, oxy, Máu, giỏ); quan (kho khả dụng, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín); README | truclamld | `chonoi/web/index.html`, `README.md` | đọc snapshot, chạy song song | AC-P1-07, AC-P1-08 |
| 6 | Test hộp đen theo AC, smoke hai tiến trình, ma trận truy vết + bằng chứng | khoa-asta | `tests/`, `docs/verification/phase-1.md`, `docs/proof/phase-1/` | song song; chạy lại ở phút 45 | tất cả |
| 7 | Clarify với Anh Năm hàng xóm | TrungHieuPh | `docs/clarify.md` | khi gặp chỗ mơ hồ | — |

**AC (rút từ DoD PRD-0):**
- AC-P1-01: hợp đồng kho có schema + ví dụ hợp lệ.
- AC-P1-02: oxy, ngạt, Máu, ngất đúng mục F (ngạt lần đầu ở t+59; nổi đúng bước thì không ngạt).
- AC-P1-03: hái, bắt cá, hold_full đúng mục F.
- AC-P1-04: smoke hai tiến trình: quán tick 0 có `stock` đúng file kho.
- AC-P1-05: khách, giữ chỗ, kiên nhẫn, uy tín khi khách bỏ đi.
- AC-P1-06: nấu → bưng → phục vụ → trả tiền, boa, đóng ca.
- AC-P1-07: HUD đọc được trong lúc chơi.
- AC-P1-08: README chạy được từ clone sạch trong ≤ 3 lệnh; test chạy bằng 1 lệnh.

## Mốc
- Phút 15: hợp đồng chốt, các lát bắt đầu.
- Phút 20: rà lát vướng, Lâm sang hỗ trợ lát 4 nếu cần.
- Phút 25: thử xuất file kho thật.
- Phút 45: smoke hai tiến trình trên `main`, QA điền ma trận.
- Phút 55: Integrator gắn tag `phase-1`.

## Rủi ro
- Lát 3 và lát 4 cùng sửa `quan.py` → chốt cấu trúc khách/đơn (mục D) trong 5 phút đầu, mỗi lát sửa vùng TODO riêng, pull --rebase thường xuyên.
- Lát 1 và lát 2 cùng sửa `GatherSim.step` → lát 1 chỉ sửa bước 2 (oxy), lát 2 chỉ sửa bước 3–4 (interact/catch).
- Windows: dùng `PYTHONPATH="tests;."` và cần lệnh `python3` (WSL hoặc alias) để smoke test chạy.
- Nhóm 6 người phải làm ≥ 2 mục mở rộng trong cả lab → chọn sau khi lõi xong.
