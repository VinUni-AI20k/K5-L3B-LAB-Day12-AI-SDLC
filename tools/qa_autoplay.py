"""QA autoplay: sinh file inputs chơi hợp lý cho gather / quan / day để làm smoke e2e.

Bot chỉ ĐỌC snapshot (như người chơi nhìn HUD) rồi quyết định input; file inputs sinh ra
được chạy lại bằng headless để lấy bằng chứng (và để kiểm tất định).

    PYTHONPATH=. python3 tools/qa_autoplay.py --mode day --days 2 --seed 1 --out-inputs in.json
    PYTHONPATH=. python3 tools/qa_autoplay.py --mode gather --seed 42 --out-inputs g.json --want ca_loc=2,bong_sung=2
    PYTHONPATH=. python3 tools/qa_autoplay.py --mode quan --seed 42 --inventory kho.json --out-inputs q.json

Không phải luật game: chỉ là công cụ kiểm thử, không import vào chonoi/.
"""

import argparse
import json
import math
from collections import Counter

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer
from chonoi.inventory import read_inventory
from chonoi.runner import Session


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _toward(p, q, stop=0.4):
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy)
    if d <= stop:
        return [0, 0]
    return [round(dx / d, 3), round(dy / d, 3)]


class Bot:
    def __init__(self, tuning, want=None, buy_order=("oxygen", "hp", "oxygen", "hp")):
        self.g = tuning["gather"]
        self.shop = tuning.get("shop", {})
        self.want_fixed = want
        self.buy_order = list(buy_order)
        self.prev = {}          # nút đã giữ ở bước trước (để tạo cạnh lên)
        self.shop_step = 0

    # ---- gather ----
    def _gather(self, sn):
        g = self.g
        pl = sn["player"]
        p = pl["pos"]
        want = Counter(self.want_fixed or sn.get("day_plan", {}).get("ingredients", {}))
        # v1.2: hold là mảng cá thể {id, kind, fresh}; v1.1 là mảng chuỗi
        have = Counter(x["kind"] if isinstance(x, dict) else x for x in sn["hold"])
        need = {k: want[k] - have[k] for k in want if want[k] > have[k]}
        room = sn["hold_capacity"] - sn["hold_count"]
        speed = g["swim_speed"] / 60.0
        dock = g["dock_pos"]
        back_ticks = _dist(p, dock) / speed + p[1] / speed + 120
        out = {"move": [0, 0]}

        if not need or room <= 0 or sn["time_left_ticks"] < back_ticks:
            if _dist(p, dock) <= g["dock_radius"] - 0.5 and p[1] <= g["surface_depth"]:
                out["interact"] = True
            else:
                out["move"] = _toward(p, dock)
            return out

        # oxy: còn ít hơn thời gian ngoi lên + đệm thì ngoi lên
        underwater = p[1] > g["surface_depth"]
        if underwater and pl["oxygen_ticks"] < p[1] / speed + 90:
            out["move"] = [0, -1]
            return out
        if not underwater and pl["oxygen_ticks"] < pl["oxygen_max_ticks"] * 0.9 and self._last_target_fish:
            return out  # đứng ở mặt nước nạp oxy trước khi lặn tiếp

        cands = []
        for n in sn["nodes"]:
            if n["ready"] and need.get(n["kind"], 0) > 0:
                cands.append((_dist(p, n["pos"]), n["id"], "node", n))
        for f in sn["fish"]:
            y = g["fish_yield"][f["kind"]]
            # chỉ lặn nếu đủ oxy cho đi + về
            if need.get(f["kind"], 0) > 0 and y <= room and f["pos"][1] / speed * 2 + 120 < pl["oxygen_ticks"]:
                cands.append((_dist(p, f["pos"]) + 3, f["id"], "fish", f))
        if not cands:
            self.want_fixed = {}  # không còn gì lấy được → về bến
            out["move"] = _toward(p, dock)
            return out
        _, _, kind, tgt = min(cands, key=lambda c: (c[0], c[1]))
        self._last_target_fish = kind == "fish"
        if kind == "node":
            if _dist(p, tgt["pos"]) <= g["interact_radius"] - 0.5 and not underwater:
                out["interact"] = True
            else:
                out["move"] = _toward(p, tgt["pos"])
        else:
            d = _dist(p, tgt["pos"])
            if d <= g["catch_radius"] - 0.4 and underwater and pl["catch_cd_ticks"] == 0:
                out["catch"] = True
            out["move"] = _toward(p, tgt["pos"], stop=0.2)
        return out

    _last_target_fish = False

    # ---- quan ----
    def _quan(self, sn):
        p = sn["player"]["pos"]
        tables = {t["id"]: t["pos"] for t in sn["tables"]}
        out = {"move": [0, 0]}
        target = None
        if sn["hand"]:
            c = [c for c in sn["customers"] if c["id"] == sn["hand"]["order_id"]]
            if c:
                target = tables[c[0]["table_id"]]
        else:
            ready = [s for s in sn["stoves"] if s["state"] == "ready"]
            idle = [s for s in sn["stoves"] if s["state"] == "idle"]
            waiting = any(c.get("order_status") == "reserved" for c in sn["customers"])
            if ready:
                target = min(ready, key=lambda s: (_dist(p, s["pos"]), s["id"]))["pos"]
            elif idle and waiting:
                target = min(idle, key=lambda s: (_dist(p, s["pos"]), s["id"]))["pos"]
        if target:
            if _dist(p, target) <= 0.4:
                out["interact"] = True
            else:
                out["move"] = _toward(p, target)
        return out

    # ---- shop ----
    def _shop(self, sn):
        self.shop_step += 1
        if self.shop_step == 1:
            ups = self.shop.get("upgrades", {})
            for kind in list(self.buy_order):
                lvl = sn["upgrades"].get(kind, 0)
                if lvl < len(ups.get(kind, [])) and ups[kind][lvl]["price"] <= sn["money"]:
                    self.buy_order.remove(kind)
                    return {"buy": kind}
            return {}
        if self.shop_step == 3:
            return {"shop_done": True}
        return {}

    def decide(self, sn):
        phase = sn.get("phase", sn.get("mode"))
        if phase != "shop":
            self.shop_step = 0
        if phase == "gather":
            out = self._gather(sn)
        elif phase == "quan":
            out = self._quan(sn)
        else:
            out = self._shop(sn)
        # cạnh lên: không giữ một nút 2 bước liên tiếp
        for b in ("interact", "catch", "shop_done"):
            v = bool(out.get(b)) and not self.prev.get(b)
            out[b] = v
            self.prev[b] = v
        return out


def autoplay(mode, seed, days=1, inventory=None, want=None, max_ticks=200000):
    t = load_contract()["tuning"]
    sess = Session(mode, t, {}, seed, inventory=inventory, days=days)
    ip = InputPlayer([], buttons=BUTTONS_V11)
    bot = Bot(t, want=want)
    frames, last, k = [], None, 0
    while not sess.done and k < max_ticks:
        fr = bot.decide(sess.snapshot())
        key = json.dumps(fr, sort_keys=True)
        if key != last or "buy" in fr:
            fr = {"tick": k, **fr}
            frames.append(fr)
            ip._frames[k] = fr
            last = key
        sess.step(ip.advance(k))
        k += 1
    return {"frames": frames}, k, sess.end_row()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--inventory")
    ap.add_argument("--want", help="gather độc lập: kind=n,kind=n")
    ap.add_argument("--out-inputs", required=True)
    a = ap.parse_args()
    want = None
    if a.want:
        want = {k: int(v) for k, v in (x.split("=") for x in a.want.split(","))}
    ver = load_contract().get("contract_version", "1.1")
    inv = read_inventory(a.inventory, contract_version=ver) if a.inventory else None
    data, ticks, end = autoplay(a.mode, a.seed, a.days, inv, want)
    with open(a.out_inputs, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"ticks={ticks} frames={len(data['frames'])} end={json.dumps(end, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
