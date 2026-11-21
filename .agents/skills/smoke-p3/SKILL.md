---
name: smoke-p3
description: Chạy smoke bàn giao kho cá thể Phase 3 (Ticket-03, Test Contract v1.2: gather --inventory-out -> quan --inventory) và lưu bằng chứng vào docs/proof/phase-3/.
---

# Smoke bàn giao kho cá thể Phase 3 (`smoke-p3`)

## Khi nào dùng
- Phút 20 của Phase 3 (bản tích hợp), và sau khi `contract_version` được bật lên `1.2`, trước khi gắn tag `phase-3`.
- Nếu `game.contract.json` còn `contract_version: "1.1"` thì kho vẫn là kho đếm: chạy `smoke-day` thay thế và ghi rõ trong verification rằng v1.2 chưa bật.

## Quy trình
1. Fixture (Ticket-03): `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}`, inputs `{"frames":[{"tick":0,"interact":true}]}`.
2. Chạy:
```powershell
python -m chonoi.headless --mode gather --seed 42 --scenario $env:TEMP\dock.json --inputs $env:TEMP\dock-inputs.json --ticks 1 --out $env:TEMP\gather.jsonl --inventory-out $env:TEMP\catch.json
python -m chonoi.headless --mode quan --seed 42 --inventory $env:TEMP\catch.json --ticks 0 --out $env:TEMP\quan.jsonl
```
3. Đạt khi: mã thoát `0` cả hai; `catch.json` có `items` là mảng; snapshot quán tick 0 có `stock` đúng id, kind, fresh của file (`100 - 1/120` sau một bước hao ở giỏ, so bằng sai số rất nhỏ).
4. Kiểm kho đếm bị từ chối ở v1.2: `{"items":{"ca_loc":1}}` với `--inventory` phải ra mã `2`.
5. `python -m unittest discover -s tests -p "test_p3_hud_qa.py" -v` chạy các test tương ứng (tự bỏ qua khi manifest còn 1.1).
6. Lưu kết quả vào `docs/proof/phase-3/` (không commit `*.jsonl`).
