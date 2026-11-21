import sys, time
sys.path.insert(0, sys.argv[1])
from chonoi.contract import load_contract
from chonoi.inventory import hold_to_individuals, counts_to_individuals
from chonoi.live import LiveGame, LiveServer
T = load_contract()["tuning"]

def fresh(items, vals):
    out = [dict(x) for x in items]
    for x, v in zip(out, vals):
        x["fresh"] = v
    return out

g = LiveGame("gather", T, {"fish": [], "monsters": [], "player": {"pos": [20, 5]}}, 1)
real_g = g.session.snapshot
hold = fresh(hold_to_individuals(["ca_loc", "ca_loc", "bong_sung", "ca_linh", "keo_neo"]), [96.5, 71.25, 28.9, 55.0, 12.0])
g.session.snapshot = lambda: {**real_g(), "hold": hold}

q = LiveGame("quan", T, {}, 1)
real_q = q.session.snapshot
stock = fresh(counts_to_individuals({"ca_loc": 2, "bong_sung": 2, "ca_linh": 1}), [88, 25, 64, 29.5, 90])
def qsnap():
    s = real_q()
    cs = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved",
           "reserved": ["I4"], "patience_ticks_left": 2400},
          {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
           "order_status": "unfulfillable", "reserved": [], "patience_ticks_left": 3000},
          {"id": "C3", "table_id": "T4", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
           "order_status": "reserved", "reserved": ["I1"], "patience_ticks_left": 3300}]
    return {**s, "stock": stock, "customers": cs}
q.session.snapshot = qsnap
for game, port in ((g, 8781), (q, 8782)):
    LiveServer(game, port=port).start()
print("up", flush=True)
time.sleep(60)
