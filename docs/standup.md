# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 — hiệu chỉnh PRD | Phạm Lý Ngọc Đức (`Ducbaynao`) | Tôi đã sửa payload `oxygen_empty/faint`, `lost` LIFO và giỏ nhận đủ lô; bổ sung test CLI, 70/70 test qua sau tích hợp TV3–5. | Tôi bàn giao nhánh `fix/ducbaynao-gather-prd-payloads`, ADR 0001 và proof mới để Integrator review. | TV6 còn thiếu handle; nhóm cần kiểm chứng DoD trên commit bàn giao trước tag. |
| Phase 3 | Lê Tuấn Đạt (`letuandat131`) | Đã review/merge PR #3 của TV4 (`hnib1908`), hoàn thành Lát 4 Quán (nấu, nhặt, phục vụ, ăn, trả tiền + tip/uy tín, kết ca `score`) và 68/68 test OK. | Bàn giao sang TV6 kiểm thử E2E toàn trình, lưu proof Phase 3–4 và đóng gói release. | Đã đồng bộ `self.tick_hz` và tiêu hao `reserved` khớp TV4; chỉ còn chỗ trống TV6 trong `TEAM.md`. |
| Phase 1 — hiệu chỉnh Quán | Vũ Văn Bình (`hnib1908`) | Đã điền TV6, cập nhật luật và payload Quán, chạy 73 test và tái hiện fixture Phase 2 ở tick 120. | Bàn giao nhánh `fix/hnib1908-phase1-quan-prd0` và ADR 0002 để Integrator review. | Chờ đối chiếu lab board và thử HUD trên trình duyệt trước khi chốt tag. |
