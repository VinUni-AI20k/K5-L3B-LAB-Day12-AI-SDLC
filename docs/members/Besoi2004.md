# Besoi2004 — phản tư cá nhân

Tôi là Nguyễn Huy Tấn (`Besoi2004`), phụ trách Dev Gather Items trong nhóm DoAnhBatDuocEm.

- **Tôi đã làm:** hoàn thành Lát 2 hái/bắt cá Phase 1 (`test_gather_items.py`) và thực hiện chuyển đổi Phase 3 (`v1.2`) cho hệ thống kho cá thể: viết [ADR 0003](../adr/0003-inventory-v12-freshness.md) và [ma trận tác động Phase 3](../plan/phase-3.md), nâng cấp `game.contract.json`, [inventory.py](../../chonoi/inventory.py) theo đơn vị nguyên `240/điểm`, cập nhật [scenario.py](../../chonoi/scenario.py), triển khai hao độ tươi `-2`/tick & sự kiện `spoiled` tại [gather.py](../../chonoi/sim/gather.py), cùng [test_freshness_gather_v12.py](../../tests/test_freshness_gather_v12.py).
- **Tôi đã review & hỗ trợ:** rà soát hành động Retro Phase 2 và cung cấp adapter kho cá thể cho `quan.py`/`day.py` giúp toàn bộ suite luôn xanh trước khi TV5 làm cháy món `burn`.
- **AI sai ở đâu và cách phát hiện:** AI suýt dùng số thực dấu phẩy động trực tiếp để kiểm ngưỡng `< 30` (có thể làm tròn `29.999` thành `30`); thử nghiệm toàn bộ `24.001` mức nguyên trong test đã ngăn sai lệch biên.
- **Điều tôi học được:** viết ADR và cập nhật toàn bộ fixture song hành khi thay đổi schema giúp chuyển phase không làm gãy nhánh chính.
