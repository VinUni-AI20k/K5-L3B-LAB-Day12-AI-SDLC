"""Soak v1.3 (TICKET-04): python3 tools/soak.py --seed 7 --days 10 --out soak.json

Một tiến trình headless chạy N Ngày liên tiếp (gather -> quan -> shop) bằng bot tham lam đọc trạng thái sim
(cùng lớp `chonoi.runner.Session` với headless/live). Ngày > 5 lặp kế hoạch D1–D5 theo ((day-1) % 5) + 1.
money / earned / reputation / cấp nâng cấp / số Ngày / id vật phẩm xuyên suốt.

Đầu ra: {"days","days_completed","crashes","results":[{"day","earned","reputation","score"}],"duration_s"};
đạt khi days_completed == days và crashes == 0. Mọi trường gameplay tất định theo seed (trừ duration_s).
Mã thoát: 0 đạt; 1 không đạt / lỗi ghi; 2 tham số sai.
"""

import argparse
import json
import math
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chonoi.contract import load_contract  # noqa: E402
from chonoi.inputs import InputState  # noqa: E402
from chonoi.runner import Session  # noqa: E402

TICK = 60
MAX_TICKS_PER_DAY = 200_000  # chốt an toàn: một Ngày dài nhất ~ (180 + quan + 10) s × 60


def _dir(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return [0.0, 0.0]
    return [dx / n, dy / n]


class Bot:
    """Bot tham lam: chỉ đọc snapshot, trả InputState cho mỗi bước."""

    def __init__(self, tuning):
        self.t = tuning
        self.g = tuning["gather"]
        self.q = tuning["quan"]
        self.prev = set()

    def _inp(self, move=(0.0, 0.0), press=(), buy=None):
        # cạnh lên: chỉ "bấm" khi bước trước không giữ nút đó
        press = set(press)
        edges = press - self.prev
        self.prev = press
        return InputState(list(move), set(press), edges, buy=buy)

    # --- gather ------------------------------------------------------------------
    def gather(self, s):
        p = s["player"]
        pos = p["pos"]
        dock = self.g["dock_pos"]
        need = dict(s["day_plan"]["ingredients"])
        for it in s["hold"]:
            if it["kind"] in need:
                need[it["kind"]] -= 1
        need = {k: v for k, v in need.items() if v > 0}
        speed = self.g["swim_speed"]
        home_ticks = math.dist(pos, dock) / speed * TICK + 90
        full = s["hold_count"] >= s["hold_capacity"]
        if not need or full or s["time_left_ticks"] <= home_ticks:
            if math.dist(pos, dock) <= self.g["dock_radius"] * 0.8:
                return self._inp(press=("interact",))
            return self._inp(_dir(pos, dock))
        # oxy: về mặt nước nếu không đủ quay lên
        up_ticks = pos[1] / speed * TICK + 60
        if not p["at_surface"] and p["oxygen_ticks"] <= up_ticks:
            return self._inp((0.0, -1.0))
        if p["at_surface"] and p["oxygen_ticks"] < p["oxygen_max_ticks"]:
            # đứng nạp oxy trước khi lặn tiếp (vẫn hái được trên mặt)
            pass
        monsters = s.get("monsters", [])

        def safe(pt):
            return all(math.dist(pt, m["pos"]) > 7 for m in monsters)

        fish = [f for f in s["fish"] if f["kind"] in need and safe(f["pos"])]
        nodes = [n for n in s["nodes"] if n["kind"] in need and n["ready"]]
        cands = [(math.dist(pos, f["pos"]), "fish", f) for f in fish]
        cands += [(math.dist(pos, n["pos"]), "node", n) for n in nodes]
        if not cands:
            # chờ ở mặt nước gần nút cần (mọc lại) hoặc về bến nếu không còn gì
            waiting = [n for n in s["nodes"] if n["kind"] in need]
            if waiting:
                n = min(waiting, key=lambda n: (n["regrow_ticks"], n["id"]))
                return self._inp(_dir(pos, [n["pos"][0], 0.0]))
            return self._inp(_dir(pos, dock))
        if p["at_surface"] and p["oxygen_ticks"] < p["oxygen_max_ticks"] and any(c[1] == "fish" for c in cands) \
                and not nodes:
            return self._inp((0.0, 0.0))
        d, kind, tgt = min(cands, key=lambda c: (c[0], c[2]["id"]))
        if kind == "node":
            if d <= self.g["interact_radius"] * 0.8 and p["at_surface"]:
                return self._inp(press=("interact",))
            return self._inp(_dir(pos, [tgt["pos"][0], 0.0]))
        if d <= self.g["catch_radius"] * 0.8 and p["catch_cd_ticks"] == 0 and not p["at_surface"]:
            return self._inp(_dir(pos, tgt["pos"]), press=("catch",))
        return self._inp(_dir(pos, tgt["pos"]))

    # --- quan ----------------------------------------------------------------------
    def quan(self, s):
        pos = s["player"]["pos"]
        r = self.q["interact_radius"] * 0.8
        target = None
        if s["hand"] is not None:
            cu = next((c for c in s["customers"] if c["id"] == s["hand"]["order_id"]), None)
            if cu is not None:
                target = next((tb["pos"] for tb in s["tables"] if tb["id"] == cu["table_id"]), None)
        if target is None and s["hand"] is None:
            ready = [st for st in s["stoves"] if st["state"] == "ready"]
            if ready:
                target = min(ready, key=lambda st: (math.dist(pos, st["pos"]), st["id"]))["pos"]
            elif any(c.get("order_status") == "reserved" for c in s["customers"]):
                idle = [st for st in s["stoves"] if st["state"] == "idle"]
                if idle:
                    target = min(idle, key=lambda st: (math.dist(pos, st["pos"]), st["id"]))["pos"]
        if target is None:
            return self._inp()
        if math.dist(pos, target) <= r:
            return self._inp(press=("interact",))
        return self._inp(_dir(pos, target))

    # --- shop ----------------------------------------------------------------------
    def shop(self, s):
        ups = self.t["shop"]["upgrades"]
        offers = []
        for name in sorted(ups):
            cur = s["upgrades"].get(name, 0)
            nxt = next((lv for lv in ups[name] if lv["level"] == cur + 1), None)
            if nxt is not None and nxt["price"] <= s["money"]:
                offers.append((nxt["price"], name))
        if offers and s["phase_tick"] < 5:
            return self._inp(buy=min(offers)[1])
        return self._inp(press=("shop_done",))

    def act(self, s):
        return getattr(self, s["phase"])(s)


def soak(seed, days, tuning=None):
    tuning = tuning or load_contract()["tuning"]
    t0 = time.monotonic()
    out = {"days": days, "days_completed": 0, "crashes": 0, "results": []}
    try:
        sess = Session("day", tuning, {}, seed, days=days)
        bot = Bot(tuning)
        ticks_today = 0
        while not sess.done:
            snap = sess.snapshot()
            events = sess.step(bot.act(snap))
            ticks_today += 1
            for ev in events:
                if ev.get("name") == "shop_end":
                    mult = tuning["score"]["reputation_multiplier"]
                    rep = sess.sim.reputation
                    out["results"].append({"day": ev["day"], "earned": sess.sim.earned, "reputation": rep,
                                           "score": sess.sim.earned + mult * math.floor(rep)})
                    ticks_today = 0
            if ticks_today > MAX_TICKS_PER_DAY:
                raise RuntimeError(f"Ngày {sess.sim.day} kẹt quá {MAX_TICKS_PER_DAY} tick")
        out["days_completed"] = sess.sim.days_completed
    except Exception:  # crash bất kỳ trong vòng chơi được đếm, không làm rơi tiến trình
        out["crashes"] += 1
        out["error"] = traceback.format_exc(limit=3)
        try:
            out["days_completed"] = sess.sim.days_completed
        except Exception:
            pass
    out["duration_s"] = round(time.monotonic() - t0, 3)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(prog="tools/soak.py")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("lỗi: --days phải >= 1\n")
        return 2
    res = soak(a.seed, a.days)
    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    ok = res["days_completed"] == res["days"] and res["crashes"] == 0
    sys.stderr.write(f"soak: days_completed={res['days_completed']}/{res['days']} crashes={res['crashes']} "
                     f"duration_s={res['duration_s']} -> {'PASS' if ok else 'FAIL'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
