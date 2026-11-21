# Smoke tích hợp Phase 2 — gather → quán

- Bản kiểm thử: `751da31`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Seed: 42.

## Fixture và lệnh chạy

`gather-scenario.json`:
```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
```

`inputs.json`:
```json
{"frames":[{"tick":0,"interact":true}]}
```

Các lệnh dưới đây dùng đường dẫn tới hai fixture trong thư mục tạm:

```powershell
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario $scenario --inputs $inputs --inventory-out $inventory --out $gatherOut
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory $inventory --out $quanOut
```

## Kết quả baseline

- Cả hai tiến trình thoát với mã 0.
- `gather_end` ở tick 1 có `reason: "docked"` và inventory `{"items":{"bong_sung":2,"ca_loc":1}}`.
- File kho xuất ra khớp inventory của sự kiện.
- Snapshot đầu của quán ở tick 0 có `stock: {"bong_sung":2,"ca_loc":1}`.
- Kết luận: đạt trên `751da31`. Chạy lại trên bản tích hợp Test Contract v1.1 để chốt kết quả bàn giao.