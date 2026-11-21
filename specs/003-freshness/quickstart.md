# Quickstart kiểm chứng Phase 3

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
# AC-P3-08: ngưỡng 30 (scenario đề)
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}' > s30.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario s30.json --out s30.jsonl && grep spoiled s30.jsonl
# AC-P3-18: smoke bàn giao file của đề → docs/proof/phase-3/
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}' > s100.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 10 --scenario s100.json --inputs dock.json --inventory-out kho.json --out g.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory kho.json --out q.jsonl
cat kho.json; head -1 q.jsonl     # stock khớp id/kind/fresh (≈ 99.992)
# AC-P3-03: kho đếm → mã 2
echo '{"items":{"ca_loc":1}}' > old.json; python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory old.json --out x.jsonl; echo $?
# AC-P3-19/20: day
python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 44400 --out d.jsonl
```
