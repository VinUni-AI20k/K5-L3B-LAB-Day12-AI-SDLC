#!/usr/bin/env bash
# Tái tạo bằng chứng Phase 2 từ gốc repo: bash docs/proof/phase-2/run_proof.sh
set -u
cd "$(dirname "$0")/../../.."
P=docs/proof/phase-2
H=(python3 -m chonoi.headless)   # = headless_cmd trong game.contract.json
TMP=$(mktemp -d)
run() { echo "\$ ${H[*]} $*"; "${H[@]}" "$@"; echo "exit=$?"; }
summ() {  # tóm tắt một JSONL: số event theo tên, các event đổi pha, dòng end
python3 - "$@" <<'PY'
import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1])]
ev = [r for r in rows if r["type"] == "event"]
keep = {"day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end", "bought", "buy_failed",
        "paused", "resumed", "faint"}
if len(sys.argv) > 2:
    open(sys.argv[2], "w").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ev if r["name"] in keep))
print("rows:", len(rows), "events:", dict(collections.Counter(r["name"] for r in ev)))
for r in ev:
    if r["name"] in keep - {"day_plan"}:
        print("  ", r["tick"], r["phase"], r.get("day"), r["name"], json.dumps(r["data"], ensure_ascii=False))
print("end:", json.dumps(rows[-1], ensure_ascii=False))
PY
}

{
echo "## 1. Smoke tích hợp gather --inventory-out -> quan --inventory (v1.1, 6 loại) — $(date '+%Y-%m-%d %H:%M') · commit $(git rev-parse --short HEAD)$(git diff --quiet HEAD -- chonoi game.contract.json || echo '+dirty')"
run --mode gather --seed 42 --scenario $P/dock.json --inputs $P/dock-inputs.json --ticks 5 --out $P/integration-gather.jsonl --inventory-out $P/integration-kho.json
echo "\$ cat $P/integration-kho.json"; cat $P/integration-kho.json
run --mode quan --seed 42 --inventory $P/integration-kho.json --ticks 0 --out $P/integration-quan.jsonl
python3 -c "
import json
kho=json.load(open('$P/integration-kho.json'))['items']
s=[json.loads(l) for l in open('$P/integration-quan.jsonl')][0]
print('quan snapshot tick', s['tick'], 'stock =', json.dumps(s['stock']), '| kho =', json.dumps(kho))
assert s['tick']==0 and s['stock']==kho; print('INTEGRATION OK')" 2>&1 | tee $P/integration.txt

echo; echo "## 2. day --days 1 (không input, không pause): trọn vòng 22.200 tick + thời gian chạy"
S=$(python3 -c 'import time;print(time.time())')
run --mode day --days 1 --seed 7 --ticks 30000 --out $TMP/day1.jsonl --snapshot-every 600
python3 -c "import time;print('elapsed_s = %.2f (yêu cầu <= 20)' % (time.time()-$S))"
summ $TMP/day1.jsonl $P/day1.events.jsonl
"${H[@]}" --mode day --days 1 --seed 7 --ticks 30000 --out $TMP/day1b.jsonl --snapshot-every 600
cmp $TMP/day1.jsonl $TMP/day1b.jsonl && echo "BYTE-IDENTICAL OK (day 1, seed 7)"

echo; echo "## 3. Nhiều Ngày: mua oxygen + hp ở Shop Ngày 1 -> chỉ áp dụng từ Ngày 2"
run --mode day --days 2 --seed 7 --scenario $P/multiday-scenario.json --inputs $P/multiday-inputs.json --ticks 50000 --out $TMP/multi.jsonl --snapshot-every 600
summ $TMP/multi.jsonl $P/multiday.events.jsonl
python3 - $TMP/multi.jsonl <<'PY' | tee $P/multiday-upgrades.txt
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
snaps = [r for r in rows if r["type"] == "snapshot"]
def show(tag, s):
    p = s.get("player", {})
    print(f"{tag}: tick={s['tick']} day={s['day']} phase={s['phase']} phase_tick={s['phase_tick']} money={s['money']} "
          f"upgrades={s['upgrades']} active={s['active_upgrades']} oxygen_max_ticks={p.get('oxygen_max_ticks')} hp_max={p.get('hp_max')}")
d1 = snaps[0]; show("Ngày 1 gather", d1)
shop = [s for s in snaps if s["phase"] == "shop" and s["day"] == 1][-1]; show("Ngày 1 shop (mở)", shop)
bought = [r for r in rows if r["type"] == "event" and r["name"] == "bought"]
for b in bought:
    print(f"bought: tick={b['tick']} day={b['day']} phase={b['phase']} {b['data']}")
d2 = next(s for s in snaps if s["day"] == 2 and s["phase"] == "gather"); show("Ngày 2 gather", d2)
assert (d1["player"]["oxygen_max_ticks"], d1["player"]["hp_max"]) == (1800, 3)
assert [(b["day"], b["data"]["upgrade"], b["data"]["level"]) for b in bought] == [(1, "oxygen", 1), (1, "hp", 1)]
assert d2["active_upgrades"] == {"hp": 1, "oxygen": 1}
assert (d2["player"]["oxygen_max_ticks"], d2["player"]["hp_max"], d2["player"]["hp"]) == (2700, 4, 4)
print("UPGRADE-NEXT-DAY OK")
PY

echo; echo "## 4. Pause trong gather của day (pause ở bước 101, resume ở bước 401): mọi mốc lùi đúng 300 tick, sim_tick vẫn 22.200"
run --mode day --days 1 --seed 7 --inputs $P/pause-inputs.json --ticks 30000 --out $TMP/pause.jsonl --snapshot-every 600
summ $TMP/pause.jsonl $P/pause.events.jsonl
} 2>&1 | tee $P/proof.txt
rm -rf "$TMP"
