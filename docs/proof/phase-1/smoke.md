# Smoke hai tiến trình — phase-1

- Thời điểm: 2026-11-21 11:18
- Commit: `454b2eb`
- Kết quả: **ĐẠT**

| Kiểm tra | Kết quả | Chi tiết |
|---|---|---|
| gather thoát mã 0 | đạt | exit 0 |
| quan thoát mã 0 | đạt | exit 0 |
| gather_end reason = docked | đạt | docked |
| file kho đúng | đạt | {"items": {"bong_sung": 2, "ca_loc": 1}} |
| file kho = gather_end.inventory | đạt |  |
| chạy lại cùng seed giống từng byte | đạt |  |
| quán tick 0 stock = file kho | đạt | {"bong_sung": 2, "ca_loc": 1} |

## Lệnh đã chạy

```
$ python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out docs/proof/phase-1/gather.jsonl --inventory-out docs/proof/phase-1/catch.json
# exit 0
$ python -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-1/catch.json --ticks 0 --out docs/proof/phase-1/quan.jsonl
# exit 0
$ python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out docs/proof/phase-1/gather-rerun.jsonl
# exit 0
```

File đầu ra: `dock.json`, `dock-inputs.json`, `gather.jsonl`, `catch.json`, `quan.jsonl` (cùng thư mục).
