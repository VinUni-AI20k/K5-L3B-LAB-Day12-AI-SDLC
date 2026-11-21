"""QA: chạy lại inputs day (5 Ngày, seed 1) trong tiến trình và kiểm các AC khó thấy qua snapshot thưa:
kho bàn giao, Shop, nâng cấp, lọc món theo day_plan, Cá Sấu (payload, LIFO, bất tử, Máu).

    PYTHONPATH=. python3 tools/qa_check_day.py docs/proof/phase-2/day5-inputs.json
"""
import copy
import json
import sys

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer
from chonoi.runner import Session

t = load_contract()["tuning"]
mcfg = t["gather"]["monsters"]
frames = json.load(open(sys.argv[1]))["frames"]
ip = InputPlayer(frames, buttons=BUTTONS_V11)
s = Session("day", t, {}, 1, days=5)
s.initial_events()
print("D1 gather: monsters %s" % [m["id"] for m in s.snapshot()["monsters"]])
last_inv = None
bad_orders, bad_hits = [], []
k = 0
while not s.done:
    # snapshot() trả tham chiếu tới trạng thái sống -> phải deepcopy để giữ "trước bước"
    before = copy.deepcopy(s.snapshot())
    evs = s.step(ip.advance(k))
    k += 1
    for e in evs:
        n = e["name"]
        if n == "gather_end":
            last_inv = e["data"]["inventory"]["items"]
        if n == "phase_start" and e["phase"] == "gather":
            sn = s.snapshot()
            print("D%d gather: monsters %s" % (e["day"], [m["id"] for m in sn["monsters"]]))
        if n == "phase_start" and e["phase"] == "quan":
            sn = s.snapshot()
            print("   quan tick0 stock==gather_end:", sn["stock"] == last_inv, "phase_tick", sn["phase_tick"])
        if n == "phase_start" and e["phase"] == "shop":
            sn = s.snapshot()
            print("   shop open: time_left", sn["time_left_ticks"], "stock", sn["stock"])
        if n == "bought":
            sn = s.snapshot()
            print("   after bought:", e["data"], "upgrades", sn["upgrades"], "active", sn["active_upgrades"])
        if n == "customer_arrived":
            plan = s.snapshot()["day_plan"]["dishes"]
            if e["data"]["dish_id"] not in plan:
                bad_orders.append((e["day"], e["data"]["dish_id"]))
        if n == "monster_hit":
            d = e["data"]
            hold = before["hold"]
            n_drop = int(len(hold) * mcfg["loss_ratio"])
            # so theo id (v1.2) hoặc kind (v1.1): độ tươi trong lost đã hao thêm 1 bước so với "trước bước"
            key = lambda x: x["id"] if isinstance(x, dict) else x
            exp_lost = [key(x) for x in reversed(hold[len(hold) - n_drop:])]
            after = s.snapshot()
            ok = (set(d) == {"monster_id", "hp", "lost", "pos"}
                  and [key(x) for x in d["lost"]] == exp_lost
                  and d["hp"] == before["player"]["hp"] - 1
                  # mục 4.5: giảm bất tử ở đầu bước, nên trước bước = 1 vẫn bị hit hợp lệ
                  and before["player"]["invuln_ticks"] <= 1
                  and after["player"]["invuln_ticks"] == mcfg["invuln_ticks"]
                  and d["pos"][1] >= t["gather"]["monsters"]["species"]["ca_sau"]["depths"][0])
            print("   monster_hit tick %d %s hp %d->%d hold %d lost %s ok=%s"
                  % (e["tick"], d["monster_id"], before["player"]["hp"], d["hp"], len(hold), [key(x) for x in d["lost"]], ok))
            if not ok:
                bad_hits.append(e)
print("orders outside day_plan:", bad_orders)
print("bad monster_hit:", bad_hits)
