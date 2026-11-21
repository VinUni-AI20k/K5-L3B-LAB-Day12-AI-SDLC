# Kiểm HUD (AC-P1-07) — phase-2

- Thời điểm: 2026-11-21 12:24
- Commit: `fe3930f`
- Lệnh: `$env:PYTHONIOENCODING="utf-8"; python3 tools/hud_check.py --phase phase-2`
- Kết quả: **CHƯA ĐẠT** — 56/57 mục kiểm

Cách kiểm: snapshot do luật sim sinh ra (headless) → vẽ HUD của `chonoi/web/index.html` bằng canvas giả (`tools/hud_harness.js`) ở 4 bề rộng 1280/900/700/480 → kiểm lỗi vẽ, chữ đè/tràn, đủ trường HUD tối thiểu của DoD, kho khả dụng tính độc lập từ snapshot. Bề rộng chữ là ước lượng (ký tự × cỡ × 0.56).

## Mục không đạt

- gather_lan_2s @480px — không chữ đè / tràn: đè: "♥♥♥" ↔ "Độ sâu 5.5 m"

## Chữ HUD hiển thị ở 1280px (theo trạng thái)

- **gather_lan_2s**: `Bến (E)` · `BUỔI SÁNG · LẶN & HÁI` · `Còn 2:58` · `Oxy 29s` · `Máu` · `♥♥♥` · `GIỎ 0/12` · `Trống` · `Độ sâu 5.5 m`
- **quan_khach_vua_den**: `BUỔI TỐI · NHÀ BÈ MÁ TƯ` · `Còn 2:58` · `Tiền 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `điên điển ×1  ·  bông súng ×4  ·  cá linh ×3  ·  cá lóc ×1` · `BẾP` · `B1: rảnh  ·  B2: rảnh` · `GỌI MÓN` · `T1: cá lóc nướng trui · 60s` · `ĐANG CẦM: Tay trống`
- **quan_bep_dang_nau**: `BUỔI TỐI · NHÀ BÈ MÁ TƯ` · `Còn 3:00` · `Tiền 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `bông súng ×4  ·  cá lóc ×2` · `BẾP` · `B1: đang nấu lẩu cá linh điên điển 7s  ·  B2: rảnh` · `GỌI MÓN` · `T1: lẩu cá linh điên điển · 42s` · `ĐANG CẦM: Tay trống`
- **quan_dang_cam_mon**: `BUỔI TỐI · NHÀ BÈ MÁ TƯ` · `Còn 3:00` · `Tiền 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `cá lóc ×2` · `BẾP` · `B1: rảnh  ·  B2: rảnh` · `GỌI MÓN` · `T1: lẩu cá linh điên điển · 15s` · `ĐANG CẦM: lẩu cá linh điên điển`
- **quan_khach_dang_an**: `BUỔI TỐI · NHÀ BÈ MÁ TƯ` · `Còn 3:00` · `Tiền 0k` · `Uy tín 4.2/5` · `Điểm 400` · `KHO KHẢ DỤNG` · `Trống` · `BẾP` · `B1: rảnh  ·  B2: rảnh` · `GỌI MÓN` · `T1: lẩu cá linh điên điển · đang ăn 5s` · `ĐANG CẦM: Tay trống`

## Toàn bộ mục kiểm

| Trạng thái | Kiểm | Kết quả | Chi tiết |
|---|---|---|---|
| gather_lan_2s @480px | không chữ đè / tràn | CHƯA ĐẠT | đè: "♥♥♥" ↔ "Độ sâu 5.5 m" |
| gather_lan_2s @700px | không chữ đè / tràn | đạt |  |
| gather_lan_2s @900px | không chữ đè / tràn | đạt |  |
| gather_lan_2s @1280px | không chữ đè / tràn | đạt |  |
| gather_lan_2s | có trường HUD: thời gian | đạt |  |
| gather_lan_2s | có trường HUD: oxy | đạt |  |
| gather_lan_2s | có trường HUD: Máu | đạt |  |
| gather_lan_2s | có trường HUD: giỏ | đạt |  |
| quan_khach_vua_den @480px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @700px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @900px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @1280px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den | có trường HUD: thời gian | đạt |  |
| quan_khach_vua_den | có trường HUD: kho khả dụng | đạt |  |
| quan_khach_vua_den | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_khach_vua_den | có trường HUD: trạng thái bếp | đạt |  |
| quan_khach_vua_den | có trường HUD: món trên tay | đạt |  |
| quan_khach_vua_den | có trường HUD: tiền | đạt |  |
| quan_khach_vua_den | có trường HUD: uy tín | đạt |  |
| quan_khach_vua_den | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'điên điển ×1  ·  bông súng ×4  ·  cá linh ×3  ·  cá lóc ×1', cần: 'điên điển ×1  ·  bông súng ×4  ·  cá linh ×3  ·  cá lóc ×1' |
| quan_bep_dang_nau @480px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @700px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @900px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @1280px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau | có trường HUD: thời gian | đạt |  |
| quan_bep_dang_nau | có trường HUD: kho khả dụng | đạt |  |
| quan_bep_dang_nau | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_bep_dang_nau | có trường HUD: trạng thái bếp | đạt |  |
| quan_bep_dang_nau | có trường HUD: món trên tay | đạt |  |
| quan_bep_dang_nau | có trường HUD: tiền | đạt |  |
| quan_bep_dang_nau | có trường HUD: uy tín | đạt |  |
| quan_bep_dang_nau | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'bông súng ×4  ·  cá lóc ×2', cần: 'bông súng ×4  ·  cá lóc ×2' |
| quan_dang_cam_mon @480px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @700px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @900px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @1280px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon | có trường HUD: thời gian | đạt |  |
| quan_dang_cam_mon | có trường HUD: kho khả dụng | đạt |  |
| quan_dang_cam_mon | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_dang_cam_mon | có trường HUD: trạng thái bếp | đạt |  |
| quan_dang_cam_mon | có trường HUD: món trên tay | đạt |  |
| quan_dang_cam_mon | có trường HUD: tiền | đạt |  |
| quan_dang_cam_mon | có trường HUD: uy tín | đạt |  |
| quan_dang_cam_mon | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'cá lóc ×2', cần: 'cá lóc ×2' |
| quan_khach_dang_an @480px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @700px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @900px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @1280px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an | có trường HUD: thời gian | đạt |  |
| quan_khach_dang_an | có trường HUD: kho khả dụng | đạt |  |
| quan_khach_dang_an | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_khach_dang_an | có trường HUD: trạng thái bếp | đạt |  |
| quan_khach_dang_an | có trường HUD: món trên tay | đạt |  |
| quan_khach_dang_an | có trường HUD: tiền | đạt |  |
| quan_khach_dang_an | có trường HUD: uy tín | đạt |  |
| quan_khach_dang_an | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'Trống', cần: 'Trống' |
| quan_khach_dang_an | khách đang ăn hiện thời gian ăn | đạt |  |
