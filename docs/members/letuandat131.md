# letuandat131 — phản tư cá nhân

Tôi là Lê Tuấn Đạt, phụ trách Dev Lead Quán (Lát 4, Phase 3).

- Tôi đã làm: [nấu bếp và nhặt món](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/9ddbce3), [phục vụ, ăn, thanh toán + tip/uy tín](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/commit/984cf2d), kết ca `quan_end` tính `score`, bộ unit/headless test trong [test_quan_service.py](../../tests/test_quan_service.py) và điền hồ sơ TV5.
- Tôi đã review và merge [PR #3 của TV4 (`hnib1908`)](https://github.com/hieunhangia/K5-L3B-LAB-Day12-AI-SDLC-DoAnhBatDuocEm/pull/3), đối chiếu [hợp đồng tích hợp](../contracts/README.md), [game.contract.json](../../game.contract.json) và [web UI](../../chonoi/web/index.html).
- AI phát hiện `test_smoke_p1` lỗi alias `python3` trên Windows (`exit 9009`), đồng thời bắt kịp việc TV4 chuẩn hóa `self.tick_hz` và `_load_customer` nên khi tích hợp Lát 4 mình đã dùng `self.tick_hz` thay vì hằng 60.0.
- Tôi học được cách giữ thứ tự tương tác tất định `(khoảng cách, bếp trước bàn, id)` và giải phóng `reserved` khi bếp bắt đầu trừ `stock` để khớp logic đặt món của TV4.
