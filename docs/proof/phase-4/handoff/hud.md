# Kiểm HUD (AC-P1-07) — phase-4/handoff

- Thời điểm: 2026-11-21 15:17
- Commit: `9bb4150`
- Lệnh: `python3 tools/hud_check.py --phase phase-4/handoff` (headless: `python -m chonoi.headless`)
- Kết quả: **ĐẠT** — 67/67 mục kiểm

Cách kiểm: snapshot do luật sim sinh ra (headless) → vẽ HUD của `chonoi/web/index.html` bằng canvas giả (`tools/hud_harness.js`) ở 4 bề rộng 1280/900/700/480 → kiểm lỗi vẽ, chữ đè/tràn, đủ trường HUD tối thiểu của DoD, kho khả dụng tính độc lập từ snapshot. Bề rộng chữ là ước lượng (ký tự × cỡ × 0.56).

## Mục không đạt

(không có)

## Chữ HUD hiển thị ở 1280px (theo trạng thái)

- **gather_lan_2s**: `BUỔI SÁNG` · `Còn 2:58` · `Oxy 29s` · `♥♥♥` · `Độ sâu 5.5 m` · `Bắt cá: sẵn sàng` · `GIỎ 2/12` · `cá linh 99% · bông súng 29% · ƯƠN`
- **quan_khach_vua_den**: `BUỔI TỐI` · `Còn 2:58` · `Tiền 0k` · `Tiền ca 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `cá lóc 97% · bông súng 74% · bông súng 74% · cá linh 89% · cá linh 89% · điên điển 99%` · `B1: rảnh  ·  B2: rảnh` · `T1: cá lóc nướng trui · 60s` · `ĐANG CẦM: Tay trống`
- **quan_bep_dang_nau**: `BUỔI TỐI` · `Còn 3:00` · `Tiền 0k` · `Tiền ca 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `cá lóc 100% · bông súng 96% · bông súng 70% · cá linh 84%` · `B1: nấu lẩu cá linh điên điển 7s  ·  B2: rảnh` · `T1: lẩu cá linh điên điển · 42s` · `ĐANG CẦM: Tay trống`
- **quan_dang_cam_mon**: `BUỔI TỐI` · `Còn 3:00` · `Tiền 0k` · `Tiền ca 0k` · `Uy tín 3.0/5` · `Điểm 300` · `KHO KHẢ DỤNG` · `cá lóc 100%` · `B1: rảnh  ·  B2: rảnh` · `T1: lẩu cá linh điên điển · 15s` · `ĐANG CẦM: lẩu cá linh điên điển`
- **quan_khach_dang_an**: `BUỔI TỐI` · `Còn 3:00` · `Tiền 0k` · `Tiền ca 0k` · `Uy tín 4.2/5` · `Điểm 400` · `KHO KHẢ DỤNG` · `cá lóc 29% · ƯƠN` · `B1: rảnh  ·  B2: rảnh` · `T1: lẩu cá linh điên điển · đang ăn 5s` · `ĐANG CẦM: Tay trống`

## Toàn bộ mục kiểm

| Trạng thái | Kiểm | Kết quả | Chi tiết |
|---|---|---|---|
| gather_lan_2s @480px | không chữ đè / tràn | đạt |  |
| gather_lan_2s @700px | không chữ đè / tràn | đạt |  |
| gather_lan_2s @900px | không chữ đè / tràn | đạt |  |
| gather_lan_2s @1280px | không chữ đè / tràn | đạt |  |
| gather_lan_2s | mọi chữ >= 18 px ở 1280 px | đạt |  |
| gather_lan_2s | có trường HUD: thời gian | đạt |  |
| gather_lan_2s | có trường HUD: oxy | đạt |  |
| gather_lan_2s | có trường HUD: Máu | đạt |  |
| gather_lan_2s | có trường HUD: giỏ | đạt |  |
| gather_lan_2s | hiện độ tươi trong giỏ / dấu hàng ươn | đạt | snapshot không có cá thể hoặc HUD thiếu %/ƯƠN |
| quan_khach_vua_den @480px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @700px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @900px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den @1280px | không chữ đè / tràn | đạt |  |
| quan_khach_vua_den | mọi chữ >= 18 px ở 1280 px | đạt |  |
| quan_khach_vua_den | có trường HUD: thời gian | đạt |  |
| quan_khach_vua_den | có trường HUD: kho khả dụng | đạt |  |
| quan_khach_vua_den | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_khach_vua_den | có trường HUD: trạng thái bếp | đạt |  |
| quan_khach_vua_den | có trường HUD: món trên tay | đạt |  |
| quan_khach_vua_den | có trường HUD: tiền | đạt |  |
| quan_khach_vua_den | có trường HUD: uy tín | đạt |  |
| quan_khach_vua_den | hiện độ tươi trong kho / dấu hàng ươn | đạt | snapshot không có cá thể hoặc HUD thiếu %/ƯƠN |
| quan_khach_vua_den | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'cá lóc 97% · bông súng 74% · bông súng 74% · cá linh 89% · cá linh 89% · điên điển 99%', cần: 'cá lóc 97% · bông súng 74% · bông súng 74% · cá linh 89% · cá linh 89% · điên điển 99%' |
| quan_bep_dang_nau @480px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @700px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @900px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau @1280px | không chữ đè / tràn | đạt |  |
| quan_bep_dang_nau | mọi chữ >= 18 px ở 1280 px | đạt |  |
| quan_bep_dang_nau | có trường HUD: thời gian | đạt |  |
| quan_bep_dang_nau | có trường HUD: kho khả dụng | đạt |  |
| quan_bep_dang_nau | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_bep_dang_nau | có trường HUD: trạng thái bếp | đạt |  |
| quan_bep_dang_nau | có trường HUD: món trên tay | đạt |  |
| quan_bep_dang_nau | có trường HUD: tiền | đạt |  |
| quan_bep_dang_nau | có trường HUD: uy tín | đạt |  |
| quan_bep_dang_nau | hiện độ tươi trong kho / dấu hàng ươn | đạt | snapshot không có cá thể hoặc HUD thiếu %/ƯƠN |
| quan_bep_dang_nau | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'cá lóc 100% · bông súng 96% · bông súng 70% · cá linh 84%', cần: 'cá lóc 100% · bông súng 96% · bông súng 70% · cá linh 84%' |
| quan_dang_cam_mon @480px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @700px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @900px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon @1280px | không chữ đè / tràn | đạt |  |
| quan_dang_cam_mon | mọi chữ >= 18 px ở 1280 px | đạt |  |
| quan_dang_cam_mon | có trường HUD: thời gian | đạt |  |
| quan_dang_cam_mon | có trường HUD: kho khả dụng | đạt |  |
| quan_dang_cam_mon | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_dang_cam_mon | có trường HUD: trạng thái bếp | đạt |  |
| quan_dang_cam_mon | có trường HUD: món trên tay | đạt |  |
| quan_dang_cam_mon | có trường HUD: tiền | đạt |  |
| quan_dang_cam_mon | có trường HUD: uy tín | đạt |  |
| quan_dang_cam_mon | hiện độ tươi trong kho / dấu hàng ươn | đạt | snapshot không có cá thể hoặc HUD thiếu %/ƯƠN |
| quan_dang_cam_mon | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'cá lóc 100%', cần: 'cá lóc 100%' |
| quan_khach_dang_an @480px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @700px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @900px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an @1280px | không chữ đè / tràn | đạt |  |
| quan_khach_dang_an | mọi chữ >= 18 px ở 1280 px | đạt |  |
| quan_khach_dang_an | có trường HUD: thời gian | đạt |  |
| quan_khach_dang_an | có trường HUD: kho khả dụng | đạt |  |
| quan_khach_dang_an | có trường HUD: món gọi + kiên nhẫn | đạt |  |
| quan_khach_dang_an | có trường HUD: trạng thái bếp | đạt |  |
| quan_khach_dang_an | có trường HUD: món trên tay | đạt |  |
| quan_khach_dang_an | có trường HUD: tiền | đạt |  |
| quan_khach_dang_an | có trường HUD: uy tín | đạt |  |
| quan_khach_dang_an | hiện độ tươi trong kho / dấu hàng ươn | đạt | snapshot không có cá thể hoặc HUD thiếu %/ƯƠN |
| quan_khach_dang_an | kho khả dụng = tồn − giữ chỗ | đạt | HUD: 'cá lóc 29% · ƯƠN', cần: 'cá lóc 29% · ƯƠN' |
| quan_khach_dang_an | khách đang ăn hiện thời gian ăn | đạt |  |
