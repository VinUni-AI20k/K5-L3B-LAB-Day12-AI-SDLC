#!/usr/bin/env bash
# Bằng chứng Phase 3 (TICKET-03 v1.2): smoke bàn giao kho cá thể, kho đếm -> mã 2, day --days 2, regression.
set -u
cd "$(dirname "$0")/../../.."
P=docs/proof/phase-3
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}' > $P/handover.scenario.json
echo '{"frames":[{"tick":0,"interact":true}]}' > $P/handover.inputs.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario $P/handover.scenario.json --inputs $P/handover.inputs.json --inventory-out $P/kho.json --out $P/gather.jsonl; echo "gather exit=$?"
python3 -m chonoi.headless --mode quan --seed 1 --inventory $P/kho.json --ticks 0 --out $P/quan.jsonl; echo "quan exit=$?"
echo '{"items":{"ca_loc":1}}' > $P/kho_count.json
python3 -m chonoi.headless --mode quan --seed 1 --inventory $P/kho_count.json --ticks 0 --out $P/quan_count.jsonl 2>$P/quan_count.err; echo "quan count-schema exit=$? (cần 2)"
python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 30000 --out $P/day2.jsonl; echo "day --days 2 exit=$?"
PYTHONPATH=tests:. python3 -m unittest discover -s tests 2>&1 | tail -3
