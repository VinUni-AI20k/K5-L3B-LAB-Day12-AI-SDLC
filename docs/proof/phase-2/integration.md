# Bằng chứng tích hợp Phase 2

- Regression trên cây làm việc: `python -m unittest discover -s tests` — 163 test đạt (`Ran 163 tests in 14.941s`, `OK`).
- Cú pháp JavaScript: kiểm tra bằng `vm.Script` — đạt. Đã chơi thử và kết quả OK; chưa có số đo cỡ chữ hoặc FPS.
- Smoke kho: `python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-2/smoke-gather-scenario.json --inputs docs/proof/phase-2/smoke-gather-inputs.json --ticks 1 --out docs/proof/phase-2/integration-gather.jsonl --inventory-out docs/proof/phase-2/integration-inventory.json`, sau đó `python -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-2/integration-inventory.json --ticks 0 --out docs/proof/phase-2/integration-quan.jsonl` — cả hai mã 0; file kho và snapshot tick 0 của quán cùng có `ca_keo: 2`, `keo_neo: 1`.
- Smoke ngày: `python -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --snapshot-every 3600 --out docs/proof/phase-2/day-smoke.jsonl` — mã 0, kết thúc `days_complete` tại tick 22200, `days_completed: 1`.
- Test bổ sung kiểm tra pause, mua/đóng Shop cùng tick, áp dụng nâng cấp ngày kế, M2 từ ngày 3 và vòng 5 ngày với fixture rút ngắn.
- Lý do sửa test cũ: `day` và `ticks=0` đã được contract v1.1 hỗ trợ; scenario có tiền đầu kỳ cần khai cả `earned`.
- Các thay đổi khung `headless.py`, `inputs.py`, `runner.py`, `scenario.py`, `inventory.py`, `live.py` và giao diện là để hỗ trợ contract v1.1 và tích hợp kho/vòng.
