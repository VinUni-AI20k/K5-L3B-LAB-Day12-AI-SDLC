# 04: Bàn giao trong `day` + Chợ + CHANGELOG

**What to build:** Vòng ngày vẫn đúng khi kho là cá thể: bàn giao cùng tick không làm hao thêm, Ngày đầu giữ id của mẫu `gather.hold`, các Ngày sau cấp id mới, và hàng mua ở Chợ nhập với độ tươi 100.

**Blocked by:** 01 (mềm: 02, 03; cần Phase 2 có `day`)

**Status:** ready-for-agent

- [ ] Bàn giao `gather → quan` trong cùng tick: hàng không hao thêm, ca quán chạy từ bước sau; id giữ nguyên.
- [ ] Ngày đầu giữ đúng id trong `gather.hold` của mẫu; các Ngày kế cấp id mới theo thứ tự mảng với `kind/fresh` ban đầu.
- [ ] Chợ Chú Sáu: hàng mua nhập riêng vào kho quán Ngày kế với `fresh: 100`, id mới, **tách** khỏi `gather_end.inventory`; hàng thô ở Shop hoặc chờ nhập không hao.
- [ ] Khi người chơi bán: lấy cá thể **chưa ươn tươi nhất** của loại, hòa theo id.
- [ ] Snapshot Shop và `stock` dùng schema cá thể, có độ tươi.
- [ ] `CHANGELOG.md`: ghi breaking change, mô tả schema mới, cách cập nhật fixture (kèm ví dụ), và điều kiện bật v1.2.
- [ ] Test: bàn giao giữ id và fresh; Ngày 2 id mới không trùng; mua ở Chợ → Ngày kế có fresh 100; bán chọn đúng cá thể.
