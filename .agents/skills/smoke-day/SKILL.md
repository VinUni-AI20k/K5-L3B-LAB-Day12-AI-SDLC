---
name: smoke-day
description: Chạy smoke Phase 2 (tích hợp gather -> quan, --mode day 1 Ngày và 2 Ngày có lệnh buy) và lưu bằng chứng sạch vào docs/proof/phase-2/.
---

# Smoke Phase 2 (`smoke-day`)

## Khi nào dùng
- Từ phút 20 của Phase 2 (smoke tích hợp) và phút 35 (smoke day), và trước khi gắn tag `phase-2`.
- Sau khi gộp lát của người khác vào `main` mà đụng `day.py`, `shop.py`, `quan.py`, `gather.py`.

## Quy trình

### Bước 1: Smoke tích hợp gather -> quan (Test Contract v1.1, kho đếm)
Dùng fixture chuẩn của Phase 1 (`docs/proof/phase-1/dock.json`, `dock-inputs.json`). Ghi `*.jsonl` và `catch.json` vào thư mục tạm.
```powershell
python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out $env:TEMP\gather.jsonl --inventory-out $env:TEMP\catch.json
python -m chonoi.headless --mode quan --seed 42 --inventory $env:TEMP\catch.json --ticks 0 --out $env:TEMP\quan.jsonl
```
Đạt khi cả hai mã thoát `0`, `catch.json` khớp `gather_end.data.inventory`, và `stock` ở snapshot quán tick 0 bằng `items` của file kho.

### Bước 2: Smoke `--mode day`
- `--days 1`: scenario `{"day":{"money":450,"earned":450},"gather":{"hold":[...],"random_fish":false}}`, inputs: `interact` ở tick 0 (cập bến), `shop_done` sau khi Shop mở. Phải có chuỗi `day_start` -> `day_plan` -> `phase_start` x 3 -> `shop_end` và dòng `end` có `reason: "days_complete"`, `days_completed: 1`.
- `--days 2` có `buy`: thêm frame `buy: "oxygen"` và một lệnh lạ (`buy: "weapon"`) trong Shop Ngày 1. Phải có `bought{upgrade: oxygen, level: 1}`, `buy_failed{reason: unknown}`, và snapshot gather đầu Ngày 2 có `active_upgrades.oxygen = 1`, `oxygen_max_ticks = 2700`.

### Bước 3: Regression
```powershell
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
```

### Bước 4: Lưu bằng chứng
Ghi vào `docs/proof/phase-2/`: `integration.txt`, `smoke-day-log.txt`, `unittest-output.txt`, kèm mã thoát, commit đã chạy và kết quả đạt hoặc chưa đạt, ghi trung thực.

## Cấm
- Không commit `*.jsonl`, không đổi `game.contract.json`, `headless_cmd`.
- Không sửa test cho xanh khi luật sai (xem `AGENTS.md`).
