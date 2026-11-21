# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** luật lõi `gather` + `quan` đúng Test Contract v1.0, hai tiến trình headless nối qua file kho,
  test 1 lệnh xanh, ma trận truy vết `docs/verification/phase-1.md`, tag `phase-1` trước 1:00.

## Việc / người / phụ thuộc (khớp `TEAM.md`)

| Mã | Việc | Người | File chính | Phụ thuộc |
|---|---|---|---|---|
| AC-P1-00 | Chốt hợp đồng kho (mục G) + danh sách sự kiện | Minh (Integrator) | `README.md` mục "Hợp đồng kho", `docs/contracts/` | — |
| AC-P1-01..06 | Lát 1: bơi/ramp, biên, dive/surface, oxy, ngạt, ngất LIFO | Minh | `chonoi/sim/gather.py` | AC-P1-00 |
| AC-P1-07..18 | Lát 2: hái, bắt cá + cooldown, cập bến, hết giờ, ghi kho | Minh | `chonoi/sim/gather.py`, `tests/test_gather_p1.py` | lát 1 |
| AC-P1-20..24 | Lát 3: lịch khách, chọn món theo seed, giữ chỗ, kiên nhẫn, `no_dish` | Duyet | `chonoi/sim/quan.py` | AC-P1-00 (kho mẫu) |
| AC-P1-30..40 | Lát 4: interact bếp/bàn, nấu/bưng/phục vụ, boa, trả tiền, đóng ca, fixture mã 2 | Duyet | `chonoi/sim/quan.py`, `tests/test_quan_p1.py` | lát 3 |
| AC-P1-41..43 | Smoke hai tiến trình, lượt đầy đủ, bằng chứng, ma trận truy vết | Nhat Minh (QA) | `docs/proof/phase-1/`, `docs/verification/phase-1.md` | lát 2 + lát 4 |
| UI | HUD gather/quán đọc snapshot | Nhat Minh | `client/` | danh sách trường snapshot (mục E) |
| Tag | Chạy lại test + proof ở commit tag, gắn `phase-1` | Minh | — | tất cả |

Gợi ý commit theo lát (mỗi người commit phần mình bằng tài khoản mình): Minh → `chonoi/sim/gather.py`,
`tests/test_gather_p1.py`; Duyet → `chonoi/sim/quan.py`, `tests/test_quan_p1.py`, `docs/clarify.md`;
Nhat Minh → `docs/proof/phase-1/*`, `docs/verification/phase-1.md`, `client/`.

## Rủi ro
- Hiểu sai thứ tự bước (mục F) → lệch tick event. Giảm rủi ro: test biên t+59, t+L, ngưỡng boa 0.5.
- Cộng dồn số thực của uy tín làm `floor(reputation)` trong điểm lệch → làm tròn 9 chữ số sau mỗi lần đổi.
- Chỗ PRD mơ hồ → ghi `docs/clarify.md`, hỏi Anh Năm trước khi đổi.
