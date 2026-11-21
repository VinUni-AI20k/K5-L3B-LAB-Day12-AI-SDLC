# Quickstart kiểm chứng Phase 2

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v            # regression P1 + test P2
# smoke tích hợp (AC-P2-31) → docs/proof/phase-2/integration.*
python3 -m chonoi.headless --mode gather --seed 7 --ticks 10800 --out g.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 7 --ticks 0 --inventory kho.json --out q.jsonl
# một Ngày (AC-P2-25, AC-P2-30)
time python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out d1.jsonl
tail -1 d1.jsonl                     # end: days_completed 1
# nhiều Ngày + nâng cấp (AC-P2-23) với scenario day.money/earned và inputs buy
python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 44400 --scenario day_rich.json --inputs buy_oxy.json --out d2.jsonl
# tất định (AC-P2-29)
python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 44400 --out a.jsonl && \
python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 44400 --out b.jsonl && cmp a.jsonl b.jsonl
grep -E '"name":"(day_start|day_plan|phase_start|shop_end|bought)"' d1.jsonl
```
