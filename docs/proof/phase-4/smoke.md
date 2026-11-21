# Smoke hai tiến trình — phase-4

- Thời điểm: 2026-11-21 14:58
- Commit: `7d9b946`
- Kết quả: **ĐẠT**

| Kiểm tra | Kết quả | Chi tiết |
|---|---|---|
| gather thoát mã 0 | đạt | exit 0 |
| quan thoát mã 0 | đạt | exit 0 |
| gather_end reason = docked | đạt | docked |
| file kho đúng id/kind, fresh hao 1 bước | đạt | {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 99.99166666666666}, {"id": "I2", "kind": "bong_sung", "fresh": 99.99166666666666}, {"id": "I3", "kind": "bong_sung", "fresh": 99.99166666666666}]} |
| file kho = gather_end.inventory (id, kind; fresh ±0.01) | đạt |  |
| chạy lại cùng seed giống từng byte | đạt |  |
| quán tick 0 stock = file kho (id, kind, fresh) | đạt | [{"id": "I1", "kind": "ca_loc", "fresh": 99.992}, {"id": "I2", "kind": "bong_sung", "fresh": 99.992}, {"id": "I3", "kind": "bong_sung", "fresh": 99.992}] |

## Lệnh đã chạy

```
$ python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-4/dock.json --inputs docs/proof/phase-4/dock-inputs.json --ticks 1 --out docs/proof/phase-4/gather.jsonl --inventory-out docs/proof/phase-4/catch.json
# exit 0
$ python3 -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-4/catch.json --ticks 0 --out docs/proof/phase-4/quan.jsonl
# exit 0
$ python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-4/dock.json --inputs docs/proof/phase-4/dock-inputs.json --ticks 1 --out docs/proof/phase-4/gather-rerun.jsonl
# exit 0
```

File đầu ra: `dock.json`, `dock-inputs.json`, `gather.jsonl`, `catch.json`, `quan.jsonl` (cùng thư mục).
