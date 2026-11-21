# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - Phase 3 (Mùa Nước Nổi)
### Added
- **Kho cá thể (Individual Items):** Chuyển đổi định dạng kho sang mảng cá thể `{id, kind, fresh}`.
- **Độ tươi & Hàng ươn (Freshness & Spoiled):**
  - Độ tươi `fresh` giảm theo thời gian; cá thể có `fresh < 30` bị coi là ươn, không thể dùng để nấu.
  - Sự kiện `spoiled` phát ra khi cá thể vượt ngưỡng ươn.
- **HUD v1.2 (Ticket 05):**
  - Hiển thị thanh độ tươi mini trên từng ô giỏ hàng.
  - Gạch chéo đỏ và nhãn `ƯƠN` cho cá thể ươn.
  - Banner toast thông báo cá thể ươn (chỉ hiện đúng 1 lần cho mỗi cá thể).
  - Cờ `?fx=0` trên URL để tắt hiệu ứng hạt và sóng nước trên máy yếu.

## [1.1.0] - Phase 2 (Một Ngày Ở Chợ Nổi — Contract v1.1)
### Added
- **Contract v1.1:** 8 đàn cá, 3 loài cá (`ca_loc`, `ca_linh`, `ca_keo`), 6 loại nguyên liệu (+`keo_neo`), thực đơn 6 món.
- **Quái vật Cá Sấu (Ticket 03):** Tuần tra 1.0 m/s, truy đuổi 3.0 m/s khi $d \ge 10$ và cách $\le 10$m, tấn công trừ 1 Máu và rơi nửa giỏ LIFO, bất tử 90 tick, recoil lùi 2m.
- **Mở rộng Quán Ăn (Ticket 04):**
  - 2 bếp nấu B1 [2,8], B2 [5,8] nấu song song độc lập không giẫm đơn nhau.
  - 4 bàn ăn T1–T4 đón khách theo nhịp $120 + 900 \cdot k$, giải phóng bàn khi khách ăn xong.
  - Thực đơn 6 món hỗ trợ đầy đủ nguyên liệu mới (`ca_keo`, `keo_neo`).
  - Hỗ trợ lọc thực đơn theo kế hoạch ngày (`day_plan.dishes`) ở chế độ `day`.
  - Phát sự kiện `no_dish` khi có bàn trống nhưng hết món đủ nguyên liệu.
- **Vòng lặp Ngày 5 Ngày:** `--mode day --days 1..5` và Shop nâng cấp bình oxy, áo phao.
- **Âm thanh tự sinh (Procedural Web Audio API):**
  - Tự động phát âm thanh khi lặn/nổi nước, hái rau, bắt cá, chuông bếp, cập bến, trả tiền, còi báo và va chạm cá sấu.
  - Nút Bật/Tắt âm thanh `🔊 / 🔇` trực tiếp trên canvas và phím tắt `M`.
- **Hiệu ứng đồ họa (VFX Particles & Ánh Sáng):**
  - Hạt bọt khí oxy nổi lên khi lặn sâu + vệt rẽ nước khi bơi nhanh.
  - Tia nắng xuyên đáy nước (God rays / Sunbeams) và ánh đèn lồng ấm cúng buổi tối.
  - Rung chấn màn hình (Screen Shake) và chữ nổi động (Floating Text).
  - Sóng nước lăn tăn nhấp nhô nhẹ trên mặt sông.

## [1.0.0] - Phase 1 (Kickoff & Core Gameplay)
### Added
- **Lõi hai buổi (contract v1.0):**
  - Lặn & hái: oxy, ngạt (choke ở `t+59`), ngất bỏ giỏ theo LIFO, hái nút + mọc lại, bắt cá (xóa đàn, hồi chiêu 30 tick), cập bến, ghi file kho.
  - Mở quán: khách đến theo lịch, giữ chỗ theo công thức, kiên nhẫn, nấc/bưng/phục vụ, boa theo ngưỡng, đóng ca.
  - Cổng kiểm một lệnh; ma trận truy vết và bằng chứng trong `docs/proof/`.
- **Giao diện HUD trực quan 2 buổi (Ticket 06):**
  - Đồng hồ đếm ngược, thanh oxy đổi 3 màu, tim Máu, giỏ hàng trực quan.
  - Hệ thống banner nhắc phím ngữ cảnh (Contextual Prompts) khi vào phạm vi bến tàu, nút rau, đàn cá, bếp nấu, bàn ăn.
  - Màn hình kết thúc ca chơi (Game Over overlay) với lý do kết thúc, bảng điểm và nút Chơi lại (hỗ trợ chuột và phím R).
  - Chuyển giao kho nguyên liệu nguyên tử giữa 2 buổi qua `inventory.json`.
