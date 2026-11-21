"""E2E TV3+TV4: tự lái Quán từ snapshot, kiểm bất biến từng tick, ghi inputs để phát lại headless.

Chạy từ gốc repo: python3 docs/proof/phase-1/tv4-e2e_quan.py <kịch bản> <inventory.json|-> <out_inputs.json> [scenario.json]
Kịch bản: serve (phục vụ hết ca) | idle (không làm gì) | late (để khách chờ lâu rồi mới nấu)
          | abandon (nhận đơn rồi bỏ mặc khách tới khi rời)
          | orphan (như abandon tới tick 3800, sau đó phục vụ lại -> tái hiện Q7)
"""
import json
import math
import sys
from collections import Counter

sys.path.insert(0, ".")
from chonoi.contract import load_contract  # noqa: E402
from chonoi.inputs import InputState  # noqa: E402
from chonoi.runner import Session  # noqa: E402

mode_name, inv_path, out_inputs = sys.argv[1], sys.argv[2], sys.argv[3]
scen_path = sys.argv[4] if len(sys.argv) > 4 else None
tuning = load_contract("game.contract.json")["tuning"]
q, menu = tuning["quan"], tuning["menu"]
inventory = json.load(open(inv_path))["items"] if inv_path != "-" else None
scenario = json.load(open(scen_path))["quan"] if scen_path else {}
sess = Session("quan", tuning, scenario, 42, inventory)
sim = sess.sim
R = q["interact_radius"]
stove, table = q["stoves"][0]["pos"], q["tables"][0]["pos"]

frames, events, problems = [], [], []
prev_move, prev_btn = [0, 0], False
pressed_last = False


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def check(tick, evs, stock_before):
    # 1. kho vật lý không âm, kho khả dụng không âm
    if any(v < 0 for v in sim.stock.values()):
        problems.append(f"t{tick}: stock âm {sim.stock}")
    if any(v < 0 for v in sim.available_stock().values()):
        problems.append(f"t{tick}: available âm {sim.available_stock()}")
    # 2. stock chỉ đổi đúng công thức khi cook_started
    expect = Counter(stock_before)
    for name, data in evs:
        if name == "cook_started":
            expect.subtract(menu[data["dish_id"]]["recipe"])
    got = Counter(sim.stock)
    if {k: v for k, v in expect.items() if v} != {k: v for k, v in got.items() if v}:
        problems.append(f"t{tick}: stock đổi sai: trước {stock_before} sự kiện {evs} sau {sim.stock}")
    # 3. reserved chỉ nằm ở khách waiting; khách khác reserved rỗng
    for c in sim.customers:
        if c["state"] != "waiting" and c["reserved"]:
            problems.append(f"t{tick}: {c['id']} state={c['state']} vẫn giữ {c['reserved']}")
    # 4. tối đa một khách / bàn
    tbl = [c["table_id"] for c in sim.customers]
    if len(tbl) != len(set(tbl)):
        problems.append(f"t{tick}: hai khách một bàn")
    # 5. hand trỏ tới đơn không còn khách
    if sim.hand and sim.hand.get("order_id") not in {c.get("order_id") for c in sim.customers}:
        problems.append(f"t{tick}: hand giữ món của đơn không còn khách {sim.hand}")


def decide(tick):
    """Trả (target_pos, muốn_interact)."""
    s = sim.stoves[0]
    waiting = [c for c in sim.customers if c["state"] == "waiting"]
    if mode_name == "idle":
        return None, False
    if mode_name == "late" and tick < 2400:
        return None, False
    if sim.hand:
        return table, True
    if s["state"] == "ready":
        if mode_name == "abandon" or (mode_name == "orphan" and tick < 3800):
            return None, False
        return stove, True
    if s["state"] == "idle" and waiting:
        return stove, True
    return None, False


while not sess.done and sess.tick < q["duration_s"] * 60 + 5:
    tick = sess.tick
    target, want = decide(tick)
    move, btn = [0, 0], False
    if target is not None:
        d = dist(sim.pos, target)
        if d > R * 0.6:
            move = [(target[0] - sim.pos[0]) / d, (target[1] - sim.pos[1]) / d]
            move = [round(m, 4) for m in move]
        elif want and not pressed_last:
            btn = True
    pressed_last = btn
    edges = {"interact"} if btn and not prev_btn else set()
    fr = {"tick": tick}
    if move != prev_move:
        fr["move"] = move
    if btn != prev_btn:
        fr["interact"] = btn
    if len(fr) > 1:
        frames.append(fr)
    prev_move, prev_btn = move, btn
    # move đi qua normalize giống InputPlayer
    n = math.hypot(*move)
    mv = (move[0] / n, move[1] / n) if n > 1 else tuple(move)
    stock_before = dict(sim.stock)
    rows = sess.step(InputState(mv, {"interact": btn}, edges))
    evs = [(r["name"], r["data"]) for r in rows]
    events.extend((r["tick"], r["name"], r["data"]) for r in rows)
    check(sess.tick, evs, stock_before)

json.dump({"frames": frames}, open(out_inputs, "w"))
cnt = Counter(e[1] for e in events)
print("ticks:", sess.tick, "done:", sim.done, "reason:", sim.reason)
print("events:", dict(sorted(cnt.items())))
print("money/earned/rep:", sim.money, sim.earned, sim.reputation, "stock cuối:", sim.stock, "hand:", sim.hand)
for t, n, d in events:
    if n in ("paid", "customer_left", "no_dish", "quan_end") or cnt[n] <= 3:
        print(f"  t{t} {n} {d}")
print("VI PHẠM:", len(problems))
seen = set()
for p in problems:
    key = p.split(":")[1][:30]
    if key not in seen:
        seen.add(key)
        print("  ", p)
