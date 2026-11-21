# hieunhangia — phản tư cá nhân

Tôi là Vũ Huy Hiệu (`hieunhangia`), Integrator và phụ trách governance/contracts trong nhóm DoAnhBatDuocEm.

- **Tôi đã làm:** hoàn thiện vòng lặp 5 Ngày trong [day.py](../../chonoi/sim/day.py) (`DaySim`, `ShopSim`), bổ sung `pause`/`resumed`, `shop_done`, `buy` và đa pha vào [inputs.py](../../chonoi/inputs.py) & [runner.py](../../chonoi/runner.py), mở `--mode day --days` trên [headless.py](../../chonoi/headless.py), [live.py](../../chonoi/live.py) và UI [index.html](../../chonoi/web/index.html), kèm bộ test [test_day_shop_pause.py](../../tests/test_day_shop_pause.py) và lưu bằng chứng Phase 2.
- **Tôi đã review & điều phối:** kiểm tra PR Phase 1 (`hnib1908`) trước khi tag `phase-1`, tích hợp PR Gather `v1.1` (`Ducbaynao`), cập nhật [docs/retro.md](../retro.md) để khóa hành động giảm xung đột schema cho Phase 3.
- **AI sai ở đâu và cách phát hiện:** AI từng phát `phase_start` với `{"phase": ...}` thay vì `{}` theo spec `v1.1`; đối chiếu bảng sự kiện và kiểm thử `test_day_shop_pause.py` đã sửa đúng trước khi merge.
- **Điều tôi học được:** thiết kế sẵn hook (`phase_tick`, `initial_events`, `(phase, day, name, data)`) ở `runner.py` giúp nối `gather -> quan -> shop` mà không nhân đôi code sim.
