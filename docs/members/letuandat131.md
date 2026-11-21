# letuandat131 — phản tư cá nhân

Tôi là Lê Tuấn Đạt (`letuandat131`), Dev Lead Quán trong nhóm DoAnhBatDuocEm.

- **Tôi đã làm:** hoàn thành Lát 4 Quán (Phase 1) và Phase 3 (`v1.2`) cho `QuanSim`: hao kho thô `-1`/tick, phát `spoiled` theo `id` trước khi tái giữ chỗ một lần (`unfulfillable`), chốt `base_price = floor(price * avg_fresh / 100)` bằng số học nguyên, mở rộng `burn` (`burn_s = 20`, `dish_burnt` tại `ready_ticks > 1200`), thanh đếm cháy trên UI, [test_quan_v12_burn.py](../../tests/test_quan_v12_burn.py), [CHANGELOG.md](../../CHANGELOG.md) và proof Phase 3.
- **Tôi đã review & hỗ trợ:** review PR #3 (`hnib1908`), phối hợp TV3 đồng bộ bàn giao `gather -> quan -> shop` giữ nguyên `id` và độ tươi.
- **AI sai ở đâu và cách phát hiện:** AI từng tính `avg_fresh` bằng số thực dễ lệch `floor`; tôi đổi sang chia nguyên `240 đv/điểm` và kiểm chứng bằng `lau_ca_linh_dien_dien`.
- **Điều tôi học được:** khóa chặt thứ tự trong tick (`timer -> hao kho -> tái giữ -> chín/cháy`) giúp mọi trường hợp biên đều tất định.
