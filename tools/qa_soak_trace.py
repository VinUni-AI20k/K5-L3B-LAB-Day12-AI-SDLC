"""QA P4: chạy lại soak trong tiến trình, ghi kế hoạch từng Ngày, dải id cá thể, nâng cấp.

    PYTHONPATH=. python3 tools/qa_soak_trace.py 7 10
"""
import json, sys
from chonoi.bot import Bot
from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputState
from chonoi.runner import Session
seed, days = int(sys.argv[1]), int(sys.argv[2])
t = load_contract()["tuning"]; plans = {p["day"]: p["dishes"] for p in t["day_plan"]}
s = Session("day", t, {}, seed, days=days); init = s.initial_events(); bot = Bot(t); held = {b: False for b in BUTTONS_V11}
allids = []; plan_ok = []
for e in init:
    if e["name"] == "day_plan": plan_ok.append(e["data"]["dishes"] == plans[1])
while not s.done:
    fr = bot.decide(s.snapshot()); edges = set()
    for b in BUTTONS_V11:
        now = bool(fr.get(b)); 
        if now and not held[b]: edges.add(b)
        held[b] = now
    for e in s.step(InputState(tuple(fr.get("move", (0, 0))), dict(held), edges, buy=fr.get("buy"))):
        if e["name"] == "day_plan":
            exp = plans[(e["day"] - 1) % 5 + 1]; plan_ok.append(e["data"]["dishes"] == exp)
        if e["name"] == "gather_end":
            ids = [x["id"] for x in e["data"]["inventory"]["items"]]; allids += ids
            print("D%-2d gather_end %-7s %s..%s (%d) | upgrades %s" % (e["day"], e["data"]["reason"], ids[0] if ids else "-", ids[-1] if ids else "-", len(ids), s.snapshot().get("active_upgrades")))
print("day_plan Ngày 1..%d khớp D((n-1)%%5+1):" % days, all(plan_ok), len(plan_ok))
print("id cá thể không trùng xuyên %d Ngày:" % days, len(allids) == len(set(allids)), "| tổng", len(allids))
