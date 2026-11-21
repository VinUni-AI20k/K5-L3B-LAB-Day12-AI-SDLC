# Ma trận truy vết Phase 1

Cách kiểm chung: `python3 tools/run_checks.py` (unit + hộp đen, smoke hai tiến trình, tất định).
Bằng chứng thô: `docs/proof/phase-1/`. Trạng thái ghi **trung thực tại thời điểm chạy** — cập nhật lại trước khi tag.

| AC | Yêu cầu (PRD §F) | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-01 | Ở mặt nước oxy không giảm, hồi 6/tick, kẹp trần | `test_oxy_mat_nuoc_khong_giam` | `docs/proof/phase-1/checks-latest.md` | chưa đạt — chưa có luật |
| AC-02 | Dưới nước −1/tick, chạm 0 phát `oxygen_empty` | `test_oxy_duoi_nuoc_ve_0_dung_tick_1800` | nt | chưa đạt |
| AC-03 | Ngạt lần đầu ở `t+59`, `choke` kèm `hp` sau trừ | `test_choke_lan_dau_o_t_plus_59` | nt | chưa đạt |
| AC-04 | `faint` bỏ giỏ LIFO, `lost` là mảng kind, kho rỗng | `test_faint_bo_gio_lifo_va_kho_rong` | nt | chưa đạt |
| AC-05 | Nổi lên đúng bước đáng lẽ ngạt thì không ngạt | `test_noi_len_dung_tick_dang_le_ngat_thi_khong_ngat` | nt | chưa đạt |
| AC-06 | Hái nút gần nhất, hòa theo `id_key`; `hold_full` giữ nút | `test_hai_nut_hoa_khoang_cach_thi_theo_id_key`, `test_gio_day_thi_hold_full_khong_dat_regrow` | nt | chưa đạt |
| AC-07 | `regrow_ticks = 1200`, `node_regrown` đúng tick | `test_moc_lai_sau_1200_tick` | nt | chưa đạt |
| AC-08 | Bắt cá xóa đàn, `yield` đúng, hồi chiêu 30 tick | `test_bat_ca_xoa_dan_va_hoi_chieu_30_tick` | nt | chưa đạt |
| AC-09 | Không có đàn trong tầm: không event, không hồi chiêu | `test_khong_co_dan_trong_tam_thi_khong_hoi_chieu` | nt | đạt (guard) |
| AC-10 | Cập bến thắng hái, không cần ở mặt nước | `test_cap_ben_thang_hai_khi_dang_lan` | nt | đạt (đã có sẵn) |
| AC-11 | Hết giờ ở mọi độ sâu: giữ giỏ, ghi kho đúng một lần | `test_het_gio_duoi_sau_van_giu_gio` | nt | đạt (đã có sẵn) |
| AC-12 | Khách đến theo `first_customer_tick`/`customer_interval_s`, giữ đúng công thức, `no_dish`, hết kiên nhẫn → mất uy tín | 4 test quán (viết sau khi ticket 01 xong) | — | chưa có |
| AC-13 | Nấu trừ kho, `ready_ticks`, bưng 1 món, phục vụ đúng đơn, boa theo ngưỡng | 4 test quán | — | chưa có |
| AC-14 | Đóng ca: khách đang ăn trả tiền, khách chờ rời `closing` không trừ uy tín, `quan_end` một lần | test quán | — | chưa có |
| AC-15 | Smoke hai tiến trình: `gather` → file kho → `quan` thấy đúng `stock` | `tools/run_checks.py` cổng 2 | nt | chưa đạt |
| AC-16 | Cùng seed → JSONL giống từng byte | `tools/run_checks.py` cổng 3 | nt | chưa đạt |

## Đánh giá ngắn

- **Đạt:** các cổng hợp đồng đã có sẵn từ starter (cập bến, hết giờ, chặn biên, xuất kho, tất định khung).
- **Chưa đạt:** toàn bộ luật gather (oxy/ngạt/ngất/hái/bắt) và luật quán — đúng như ticket 02–05.
- **Điều cần chỉnh cho phase sau:** khi 01 xong, viết ngay 4 test quán (AC-12..14) để QA không chờ; trước khi tag phải chạy lại `tools/run_checks.py` và cập nhật cột Kết quả.

## Cập nhật sau PR #1 (`a749b76`, merge `9342f9e`)

Commit của Cao Minh làm xanh 3/8 test đỏ: oxy, `oxygen_empty`, `choke` đúng `t+59` (case ngập từ đầu),
`dive`/`surface`, không ngạt khi nổi lên. Còn **5 đỏ**:

| Test | Trạng thái | Ghi chú |
|---|---|---|
| `choke_lan_dau_o_t_plus_59` | ✅ | choke ở 1859 |
| `oxy_duoi_nuoc_ve_0_dung_tick_1800` | ✅ | |
| `noi_len_dung_tick_dang_le_ngat_thi_khong_ngat` | ✅ | |
| `faint_bo_gio_lifo_va_kho_rong` | ❌ | `choke` ở tick **60** thay vì 59 khi scenario bắt đầu với oxy = 0. PRD nói "t+59"; cần chốt với Anh Năm: mốc `t` là tick chạm 0 trong lượt, hay trạng thái sẵn có ở tick 0? |
| `hai_nut_hoa_khoang_cach_thi_theo_id_key` | ❌ | lát 2 (Nhật Minh) |
| `gio_day_thi_hold_full_khong_dat_regrow` | ❌ | lát 2 |
| `moc_lai_sau_1200_tick` | ❌ | lát 2 |
| `bat_ca_xoa_dan_va_hoi_chieu_30_tick` | ❌ | lát 2 |

Cổng tích hợp và tất định: **PASS** (`tools/run_checks.py`). Fixture quán đầy đủ (`customers`/`hand`/`stoves`) đã nạp được
sau commit prefactor; 4 test quán vẫn `skip` vì luật quán chưa có.

## Cập nhật sau lát 2 (`gather_actions`)

`tools/run_checks.py` → **PASS**. 53 test (49 chạy + 4 skip), 0 đỏ.

| Nhóm AC | Kết quả |
|---|---|
| AC-01..AC-11 (oxy, ngạt, ngất, hái, mọc lại, bắt cá, cập bến, hết giờ) | ✅ đạt |
| AC-15 smoke hai tiến trình | ✅ đạt (35823 byte, kho đúng) |
| AC-16 tất định cùng seed | ✅ đạt |
| AC-12..AC-14 (khách, nấu/phục vụ, đóng ca) | ⏳ 4 test đang `skip`, chờ luật quán |

Ghi chú: hai chỗ PRD mơ hồ đã chốt tạm và ghi vào `docs/clarify.md` (Q9 ngạt khi fixture đặt sẵn oxy 0 → 60;
Q10 nút mọc lại ở `tick_hái + 1200`). Nếu Anh Năm trả lời khác thì sửa test + luật, không sửa bằng chứng.

## Cập nhật sau lát 3 (`quan_customers`)

Quán đã có khách: đến theo `phase_tick` (120, 1020, …), chọn đều theo seed trong món đủ nguyên liệu khả dụng
(tồn − giữ chỗ), giữ đúng công thức ngay khi gọi, kiên nhẫn giảm từ bước sau, hết kiên nhẫn thì rời và uy tín −0.5,
có bàn trống mà hết món thì `no_dish`. Mới 3/5 test quán xanh; 2 test bếp/phục vụ vẫn `skip` (ticket 05 của Đức Minh).

`AC-12` (khách/giữ chỗ/kiên nhẫn/no_dish) → **đạt**. `AC-13`, `AC-14` (nấu/bưng/phục vụ/tiền, đóng ca) → chưa.
