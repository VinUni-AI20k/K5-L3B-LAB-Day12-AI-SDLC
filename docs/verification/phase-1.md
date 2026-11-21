# Ma trận truy vết Phase 1 — contract v1.0 (đã tag `phase-1`)

Cách kiểm chung: `python3 tools/run_checks.py` (unittest + smoke hai tiến trình + tất định byte).
Bằng chứng thô: `docs/proof/phase-1/`. Cột Kết quả ghi **trạng thái thật tại commit kiểm** — cập nhật lại trước mỗi tag.

## Luật lõi (PRD §F)

| AC | Yêu cầu | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-01 | Ở mặt nước oxy không giảm, hồi 6/tick, kẹp trần | `test_oxy_mat_nuoc_khong_giam` | `checks-latest.md` | đạt |
| AC-02 | Dưới nước −1/tick, chạm 0 phát `oxygen_empty` | `test_oxy_duoi_nuoc_ve_0_dung_tick_1800` | nt | đạt |
| AC-03 | Ngạt lần đầu ở `t+59`, `choke` kèm `hp` sau trừ | `test_choke_lan_dau_o_t_plus_59` | nt | đạt |
| AC-04 | `faint` bỏ giỏ LIFO, `lost` là mảng kind, kho rỗng | `test_faint_bo_gio_lifo_va_kho_rong` | nt | đạt (fixture đặt sẵn oxy 0 ⇒ ngạt ở 60, xem `docs/clarify.md` Q9) |
| AC-05 | Nổi lên đúng bước đáng lẽ ngạt thì không ngạt | `test_noi_len_dung_tick_dang_le_ngat_thi_khong_ngat` | nt | đạt |
| AC-06 | Hái nút gần nhất, hòa theo `id_key`; `hold_full` giữ nút | `test_hai_nut_hoa_khoang_cach_thi_theo_id_key`, `test_gio_day_thi_hold_full_khong_dat_regrow` | nt | đạt |
| AC-07 | `regrow_ticks = 1200`, `node_regrown` ở `tick_hái + 1200` | `test_moc_lai_sau_1200_tick` | nt | đạt |
| AC-08 | Bắt cá xóa đàn, `yield` đúng, hồi chiêu 30 tick | `test_bat_ca_xoa_dan_va_hoi_chieu_30_tick` | nt | đạt |
| AC-09 | Không có đàn trong tầm: không event, không hồi chiêu | `test_khong_co_dan_trong_tam_thi_khong_hoi_chieu` | nt | đạt |
| AC-10 | Cập bến thắng hái, không cần ở mặt nước | `test_cap_ben_thang_hai_khi_dang_lan` | nt | đạt |
| AC-11 | Hết giờ ở mọi độ sâu: giữ giỏ, ghi kho đúng một lần | `test_het_gio_duoi_sau_van_giu_gio` | nt | đạt |
| AC-12 | Khách đến theo lịch, giữ đúng công thức, `no_dish`, hết kiên nhẫn → mất uy tín | `test_khach_den_tick_120_va_giu_cho`, `test_het_kien_nhan_thi_roi_va_mat_uy_tin`, `test_het_kho_thi_no_dish` | nt | đạt |
| AC-13 | Nấu trừ kho, `ready_ticks`, bưng 1 món, phục vụ đúng đơn, boa theo ngưỡng | `test_nau_dung_don_va_chin_sau_cook_s`, `test_phuc_vu_dung_don_thi_tra_tien_va_boa` | nt | đạt |
| AC-14 | Đóng ca: khách đang ăn trả tiền, khách chờ rời `closing` không trừ uy tín, `quan_end` một lần | `test_dong_ca_tra_tien_khach_cho_roi_va_mot_quan_end` | nt | đạt |
| AC-15 | Smoke hai tiến trình: `gather` → file kho → `quan` thấy đúng `stock` | `tools/run_checks.py` cổng 2 | nt | đạt |
| AC-16 | Cùng seed → JSONL giống từng byte | `tools/run_checks.py` cổng 3 | nt | đạt |

## HUD (ticket 06 — Vinh)

| AC | Cách kiểm | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-HUD-01 HUD sáng: thời gian, oxy đổi màu, Máu, giỏ, prompt bến/nút/cá | chơi thử live `gather` | `docs/proof/phase-1/hud-ui.md` | đạt |
| AC-HUD-02 HUD tối: kho, khách + kiên nhẫn, bếp + timer, tay, tiền, uy tín | chơi thử live `quan` | nt | đạt |
| AC-HUD-03 Màn kết thúc: lý do `docked`/`time`/`fainted`, điểm, chơi lại (chuột + `R`) | chạy hết giờ / cập bến / ngạt | nt | đạt |
| AC-HUD-04 Null-safety khi thiếu trường; headless không đổi byte | `tools/run_checks.py` cổng 3 | `checks-latest.md` | đạt |

> **Ghi chú khôi phục:** hai file proof HUD (`docs/proof/phase-1/hud-ui.md`, `docs/proof/phase-3/hud-do-tuoi.md`)
> từng bị xoá ở commit `62add6e` ("fix qa") và đã được khôi phục từ `62add6e^`. Ảnh trong đó chụp **trước**
> commit `f4ea51b` (thêm chế độ tương phản cao), nên cần chụp lại ở Phase 4 — nội dung mô tả vẫn đúng.

## Đánh giá ngắn

- **Đạt:** toàn bộ 16 AC luật + 4 AC HUD; 185 test xanh trên `main` (191 khi merge PR #13 nối hook net).
- **Ghi chú:** AC-04 dùng mốc 60 cho fixture "đặt sẵn oxy 0" — đã ghi giả định ở `docs/clarify.md` Q9, ca ngập từ oxy đầy vẫn đúng `t+59`.
- **Điều cần chỉnh:** trước tag Phase 4, chụp lại ảnh HUD sau khi có tương phản cao; cập nhật lại bảng nếu Phase 2 đổi số liệu.
