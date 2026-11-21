"""QA: chạy lại inputs day (5 Ngày, seed 1) trong tiến trình, kiểm kho bàn giao, Shop, nâng cấp, lọc món theo day_plan.

    PYTHONPATH=. python3 tools/qa_check_day.py docs/proof/phase-2/day5-inputs.json
"""
import json,sys
from chonoi.contract import load_contract
from chonoi.runner import Session
from chonoi.inputs import BUTTONS_V11, InputPlayer
t=load_contract()["tuning"]
frames=json.load(open(sys.argv[1]))["frames"]
ip=InputPlayer(frames,buttons=BUTTONS_V11)
s=Session("day",t,{},1,days=5)
s.initial_events()
last_inv=None; bad=[]; k=0
while not s.done:
    evs=s.step(ip.advance(k)); k+=1
    for e in evs:
        n=e["name"]
        if n=="gather_end": last_inv=e["data"]["inventory"]["items"]
        if n=="phase_start" and e["phase"]=="quan":
            sn=s.snapshot(); print("D%d quan tick0 stock==gather_end:"%e["day"], sn["stock"]==last_inv, "phase_tick", sn["phase_tick"])
        if n=="phase_start" and e["phase"]=="shop":
            sn=s.snapshot(); print("   shop open: time_left", sn["time_left_ticks"], "stock", sn["stock"])
        if n=="bought":
            sn=s.snapshot(); print("   after bought:", e["data"], "upgrades", sn["upgrades"], "active", sn["active_upgrades"])
        if n=="customer_arrived":
            plan=s.snapshot()["day_plan"]["dishes"]
            if e["data"]["dish_id"] not in plan: bad.append((e["day"], e["data"]["dish_id"]))
print("orders outside day_plan:", bad)
