# Smoke tích hợp Phase 2: gather → file kho → quan

Chạy trên nhánh `huydn8816` (đã gộp `main` e08683e), `contract_version` 1.0, Python 3.14 trên Windows (cần `PYTHONUTF8=1` khi chuyển hướng đầu ra).

```
python3 -m chonoi.headless --mode gather --seed 42 --inputs docs/proof/phase-2/integration.inputs.json \
    --ticks 400 --out docs/proof/phase-2/integration.gather.jsonl --inventory-out docs/proof/phase-2/integration.inventory.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-2/integration.inventory.json \
    --ticks 0 --out docs/proof/phase-2/integration.quan.jsonl
```

Kịch bản trong `integration.inputs.json`: bơi mặt nước từ bến sang N1 (tick 0–140), hái (interact tick 145), quay về (tick 150–250), cập bến (interact tick 260).

Kết quả:
- Mã thoát cả hai lệnh: 0.
- `gather`: event `gather` ở tick 146 `{node_id:N1, kind:bong_dien_dien, amount:1}`, event `gather_end` ở tick 261 `reason:docked`, inventory `{"items":{"bong_dien_dien":1}}`.
- `integration.inventory.json` = `{"items":{"bong_dien_dien":1}}`, khớp `gather_end.inventory`.
- `quan` snapshot tick 0: `stock = {"bong_dien_dien": 1}` (đúng nội dung file tiến trình đầu).
- Tất định: chạy lại lệnh `gather` ra file khác, `cmp` JSONL và file kho đều giống từng byte.

Chưa kiểm: luồng `--mode day` (chưa có trong code), nên chưa có bằng chứng bàn giao trong bộ nhớ giữa các buổi.
