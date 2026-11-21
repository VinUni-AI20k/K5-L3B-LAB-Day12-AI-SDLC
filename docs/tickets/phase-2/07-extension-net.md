# 07: Mở rộng — Vợt hút cá (net)

**What to build:** Nâng cấp Vợt cho phép bắt nhiều đàn trong một lần bấm: bán kính rộng hơn, tối đa 2–3 đàn, duyệt theo id. Đây là mục **mở rộng bắt buộc tối thiểu 1** cho nhóm 5 người.

**Blocked by:** 02, 05

**Status:** ready-for-agent

- [ ] Manifest có `extensions: ["net"]` và `shop.upgrades.net` hai cấp: 250 → bán kính 4.0 m, tối đa 2 đàn; 500 → 6.0 m, tối đa 3 đàn.
- [ ] Cấp 0 dùng đúng luật lõi (đàn gần nhất trong `catch_radius`, hòa theo id).
- [ ] Từ cấp 1: duyệt đàn theo id trong bán kính vợt; đàn không đủ chỗ phát `hold_full` và **giữ lại**, vẫn xét đàn kế; dừng khi đủ `max_schools` lần bắt thành công.
- [ ] Hồi chiêu chỉ đặt khi có ít nhất một đàn bắt thành công; không có đàn nào → không event, không hồi chiêu.
- [ ] Không bật extension → hành vi y như lõi (hidden test mặc định không thấy khác biệt).
- [ ] Có test: hai cấp, giỏ gần đầy, không có đàn trong tầm, và so byte với cấu hình không bật extension.
