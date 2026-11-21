#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
sha="$(git rev-parse --short HEAD)"
out="docs/proof/phase-1/smoke-${sha}"
# Không ghi đè bằng chứng đã có của cùng commit.
if [[ -e "$out" ]]; then
    echo "Đã có bằng chứng cho commit $sha ở $out — không ghi đè. Xóa thư mục đó nếu muốn chạy lại." >&2
    exit 1
fi
mkdir "$out"
summary="$out/summary.txt"
printf 'sha: %s\ntime_utc: %s\n' "$(git rev-parse HEAD)" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$summary"
failed=0
record() {
    local result="$1" label="$2"
    printf '%s %s\n' "$result" "$label" | tee -a "$summary"
    if [[ "$result" == FAIL ]]; then failed=1; fi
}
check() {
    local label="$1"
    shift
    if "$@"; then record PASS "$label"; else record FAIL "$label"; fi
}
if headless_cmd="$(python3 -c 'import json; print(json.load(open("game.contract.json", encoding="utf-8"))["headless_cmd"])')"; then
    record PASS headless_cmd
else
    record FAIL headless_cmd
    exit 1
fi
# shlex.split giữ đối số có dấu cách; không eval chuỗi lệnh trong contract.
headless() {
    python3 -c 'import shlex, subprocess, sys; sys.exit(subprocess.call(shlex.split(sys.argv[1]) + sys.argv[2:]))' "$headless_cmd" "$@"
}
printf '%s\n' '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > "$out/dock.json"
printf '%s\n' '{"frames":[{"tick":0,"interact":true}]}' > "$out/dock-inputs.json"
check gather_process headless --mode gather --seed 42 --scenario "$out/dock.json" --inputs "$out/dock-inputs.json" --ticks 1 --out "$out/gather.jsonl" --inventory-out "$out/catch.json"
check quan_process headless --mode quan --seed 42 --inventory "$out/catch.json" --ticks 0 --out "$out/quan.jsonl"
check catch_schema_and_items python3 -c 'import json,sys; assert json.load(open(sys.argv[1])) == {"items":{"bong_sung":2,"ca_loc":1}}' "$out/catch.json"
check quan_tick_zero_stock python3 -c 'import json,sys; rows=[json.loads(s) for s in open(sys.argv[1]) if s.strip()]; ss=[r for r in rows if r.get("type")=="snapshot" and r.get("tick")==0]; assert len(ss)==1; assert ss[0].get("stock")=={"bong_sung":2,"ca_loc":1}' "$out/quan.jsonl"
check gather_end_docked python3 -c 'import json,sys; rows=[json.loads(s) for s in open(sys.argv[1]) if s.strip()]; es=[r for r in rows if r.get("type")=="event" and r.get("name")=="gather_end"]; assert len(es)==1; assert es[0].get("data")=={"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}' "$out/gather.jsonl"
# Lượt gather thứ hai có cùng tất cả tham số logic; chỉ đổi đường dẫn đầu ra.
check repeat_gather_process headless --mode gather --seed 42 --scenario "$out/dock.json" --inputs "$out/dock-inputs.json" --ticks 1 --out "$out/gather-repeat.jsonl" --inventory-out "$out/catch-repeat.json"
check deterministic_jsonl cmp -s "$out/gather.jsonl" "$out/gather-repeat.jsonl"
check deterministic_inventory cmp -s "$out/catch.json" "$out/catch-repeat.json"
if PYTHONPATH=tests:. python3 -m unittest discover -s tests -v > "$out/test.log" 2>&1; then
    record PASS unittest
else
    record FAIL unittest
fi
printf 'Evidence: %s\n' "$out"
exit "$failed"
