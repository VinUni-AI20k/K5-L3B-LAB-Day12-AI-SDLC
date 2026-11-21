#!/usr/bin/env bash
# Tái tạo bằng chứng Phase 1 từ gốc repo: bash docs/proof/phase-1/run_proof.sh
set -u
cd "$(dirname "$0")/../../.."
P=docs/proof/phase-1
H=(python3 -m chonoi.headless)   # = headless_cmd trong game.contract.json
TMP=$(mktemp -d)
run() { echo "\$ ${H[*]} $*"; "${H[@]}" "$@"; echo "exit=$?"; }

{
echo "## Smoke hộp đen (Test Contract G) — $(date '+%Y-%m-%d %H:%M') · commit $(git rev-parse --short HEAD)$(git diff --quiet HEAD -- chonoi || echo '+dirty')"
run --mode gather --seed 42 --scenario $P/dock.json --inputs $P/dock-inputs.json --ticks 1 --out $P/smoke-gather.jsonl --inventory-out $P/catch.json
echo "\$ cat $P/catch.json"; cat $P/catch.json
run --mode quan --seed 42 --inventory $P/catch.json --ticks 0 --out $P/smoke-quan.jsonl
python3 -c "import json;r=[json.loads(l) for l in open('$P/smoke-quan.jsonl')];s=r[0];print('quan snapshot tick', s['tick'], 'stock =', json.dumps(s['stock']));assert s['stock']=={'bong_sung':2,'ca_loc':1};print('SMOKE OK')"

echo; echo "## Lượt đầy đủ 10800 tick (preset, có điều khiển) — gather rồi quán qua file kho"
run --mode gather --seed 7 --inputs $P/full-gather-inputs.json --ticks 10800 --out $TMP/full-gather.jsonl --inventory-out $P/full-kho.json --snapshot-every 600
echo "\$ cat $P/full-kho.json"; cat $P/full-kho.json
run --mode quan --seed 7 --inventory $P/full-kho.json --inputs $P/full-quan-inputs.json --ticks 10800 --out $TMP/full-quan.jsonl --snapshot-every 600
for m in gather quan; do
  python3 - "$TMP/full-$m.jsonl" "$P/full-$m.events.jsonl" <<'PY'
import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1])]
ev = [r for r in rows if r["type"] == "event"]
open(sys.argv[2], "w").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ev + [rows[-1]]))
print(sys.argv[1].split("/")[-1], "rows:", len(rows), "events:", dict(collections.Counter(r["name"] for r in ev)))
print("end:", json.dumps(rows[-1], ensure_ascii=False))
PY
done
echo; echo "## Tất định: chạy lại gather cùng seed/input -> so byte"
"${H[@]}" --mode gather --seed 7 --inputs $P/full-gather-inputs.json --ticks 10800 --out $TMP/again.jsonl --snapshot-every 600
cmp $TMP/full-gather.jsonl $TMP/again.jsonl && echo "BYTE-IDENTICAL OK"
} 2>&1 | tee $P/proof.txt
rm -rf "$TMP"
