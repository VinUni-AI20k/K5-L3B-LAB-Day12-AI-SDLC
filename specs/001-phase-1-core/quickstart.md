# Quickstart kiểm chứng Phase 1

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
# gather → kho → quan
python3 -m chonoi.headless --mode gather --seed 1 --ticks 10800 --out g.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 1 --ticks 10800 --inventory kho.json --out q.jsonl
# tất định (AC-P1-22)
python3 -m chonoi.headless --mode quan --seed 1 --ticks 10800 --inventory kho.json --out q2.jsonl && cmp q.jsonl q2.jsonl
# lọc sự kiện
grep '"type":"event"' q.jsonl | head
```

Kịch bản theo AC: xem bảng AC trong [spec.md](spec.md); scenario mẫu lưu ở `docs/proof/phase-1/` (TV5).
Kỳ vọng: test xanh; `cmp` không in gì; `kho.json` khớp `gather_end.data.inventory`.
