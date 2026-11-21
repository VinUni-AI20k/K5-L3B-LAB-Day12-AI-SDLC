#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
proof_dir="${1:-docs/proof/phase-2/smoke-local}"
mkdir -p "$proof_dir"
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v > "$proof_dir/tests.log" 2>&1
python3 - "$proof_dir" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

out=Path(sys.argv[1])
def write(name, data):
    p=out/name
    p.write_text(json.dumps(data,ensure_ascii=False)+'\n')
    return str(p)
def run(mode,name,ticks=1,**flags):
    p=out/name
    cmd=[sys.executable,'-m','chonoi.headless','--mode',mode,'--seed','42','--ticks',str(ticks),'--out',str(p)]
    for key,value in flags.items():cmd += ['--'+key.replace('_','-'),str(value)]
    start=time.perf_counter()
    subprocess.run(cmd,check=True)
    return p,time.perf_counter()-start
scenario=write('dock.json',{'gather':{'hold':['ca_loc','bong_sung','bong_sung'],'random_fish':False}})
inputs=write('dock-inputs.json',{'frames':[{'tick':0,'interact':True}]})
inventory=str(out/'inventory.json')
run('gather','gather.jsonl',scenario=scenario,inputs=inputs,inventory_out=inventory)
p,_=run('quan','quan.jsonl',ticks=0,inventory=inventory)
assert json.loads(p.read_text().splitlines()[0])['stock']=={'bong_sung':2,'ca_loc':1}
p,elapsed=run('day','day.jsonl',22200,days=1,snapshot_every=600)
r,_=run('day','day-repeat.jsonl',22200,days=1,snapshot_every=600)
assert p.read_bytes()==r.read_bytes()
end=json.loads(p.read_text().splitlines()[-1])
assert end['reason']=='days_complete' and end['days_completed']==1 and end['sim_tick']==22200
assert elapsed <= 20, elapsed
scenario=write('upgrade-scenario.json',{'day':{'money':450,'earned':450},'gather':{'time_left_ticks':1,'random_fish':False},'quan':{'time_left_ticks':1}})
inputs=write('upgrade-inputs.json',{'frames':[{'tick':2,'buy':'oxygen'},{'tick':3,'buy':'hp'},{'tick':4,'shop_done':True}]})
p,_=run('day','upgrade-day.jsonl',22200,days=2,scenario=scenario,inputs=inputs,snapshot_every=1)
rows=[json.loads(line) for line in p.read_text().splitlines()]
start=next(row for row in rows if row['type']=='snapshot' and row['day']==2)
assert start['player']['oxygen_ticks']==2700 and start['player']['hp']==4
assert start['money']==0 and start['earned']==450 and start['score']==750
assert start['upgrades']==start['active_upgrades']=={'oxygen':1,'hp':1}
assert rows[-1]['days_completed']==2 and rows[-1]['reason']=='days_complete'
summary={'base_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
         'working_tree_may_include_changes':True,'one_day_ticks':end['sim_tick'],
         'one_day_elapsed_s':round(elapsed,3),'same_seed_same_bytes':True,
         'day_sha256':hashlib.sha256(r.read_bytes()).hexdigest(),
         'integration':'gather inventory equals quan stock','upgrade_next_day':'2700 oxygen, 4 hp; money 0; earned 450; score 750'}
write('summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
PY
