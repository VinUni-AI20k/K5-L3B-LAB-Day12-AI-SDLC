# Smoke bàn giao kho Phase 2

- Fixture/luật v1.1 từ `ac0bdd8`; smoke được chạy lại trên `fe3930f` sau khi tích hợp Phase 2.
- Luồng kiểm: `gather --inventory-out` → `quan --inventory`, `--seed 42`.
- Fixture đặt sẵn trong giỏ tại bến, tắt cá ngẫu nhiên; smoke này kiểm giao thức xuất/đọc kho, không kiểm bắt cá, cá bơi/sinh hoặc quái.

## Lệnh

```powershell
python3 -m chonoi.headless --mode gather --seed 42 --scenario docs\proof\phase-2\integration.gather.json --inputs docs\proof\phase-2\integration.inputs.json --ticks 1 --out docs\proof\phase-2\integration.gather.jsonl --inventory-out docs\proof\phase-2\integration.inventory.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory docs\proof\phase-2\integration.inventory.json --ticks 0 --out docs\proof\phase-2\integration.quan.jsonl
```

## Kết quả

- Gather thoát mã 0; `gather_end` ở tick 1 có `reason: "docked"`.
- `gather_end.data.inventory` và file inventory giống nhau:
  `{"items":{"bong_sung":2,"ca_keo":1,"ca_loc":1,"keo_neo":1}}`.
- Snapshot quan tick 0 nhận đúng `stock` với bốn loại và số lượng tương ứng.
- Kết quả: **ĐẠT** cho luồng bàn giao file kho với các kind v1.1.
- Artifact: `integration.gather.json`, `integration.inputs.json`, `integration.gather.jsonl`, `integration.inventory.json`, `integration.quan.jsonl`.
