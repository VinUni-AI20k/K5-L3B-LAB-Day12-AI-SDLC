"""Soak headless (Test Contract v1.3): chạy N Ngày trong MỘT tiến trình bằng bot tất định.

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Mỗi Ngày đi qua gather -> quan -> shop. Kế hoạch D1–D5 lặp ở Ngày 6–10. Tiền, tổng thu, uy tín,
cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt (cùng một Session `day`).

soak.json = {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}
  - results[] ghi tại lúc Shop đóng (event shop_end).
  - duration_s là thời gian thực (không dùng để so tất định); mọi trường khác chỉ phụ thuộc seed.
Mã thoát: 0 khi days_completed == days và crashes == 0; 1 khi có crash / chưa xong; 2 khi tham số sai.
Không ghi bảng xếp hạng.
"""

import argparse
import json
import sys
import time
import traceback

from .bot import Bot
from .contract import load_contract
from .errors import BadInput
from .inputs import BUTTONS_V11, InputState
from .runner import Session

TICKS_PER_DAY_CAP = 22_200  # Ngày không pause dài tối đa 22.200 tick (TICKET-02)


def _positive_int(name):
    def conv(s):
        try:
            v = int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"--{name} phải là số nguyên")
        return v
    return conv


def run_soak(seed: int, days: int, tuning=None):
    """Chạy soak, trả dict soak.json (không gồm duration_s)."""
    tuning = tuning or load_contract()["tuning"]
    out = {"days": days, "days_completed": 0, "crashes": 0, "results": []}
    try:
        sess = Session("day", tuning, {}, seed, days=days)
        sess.initial_events()
        bot = Bot(tuning)
        held = {b: False for b in BUTTONS_V11}
        max_ticks = days * TICKS_PER_DAY_CAP * 2  # chặn vòng lặp vô hạn nếu luật kẹt
        k = 0
        while not sess.done and k < max_ticks:
            fr = bot.decide(sess.snapshot())
            move = tuple(float(c) for c in fr.get("move", (0, 0)))
            edges = set()
            for b in BUTTONS_V11:
                now = bool(fr.get(b, False))
                if now and not held[b]:
                    edges.add(b)
                held[b] = now
            for e in sess.step(InputState(move, dict(held), edges, buy=fr.get("buy"))):
                if e["name"] == "shop_end":
                    snap = sess.snapshot()
                    out["results"].append({"day": e["day"], "earned": snap["earned"],
                                           "reputation": snap["reputation"], "score": snap["score"]})
            k += 1
        out["days_completed"] = sess.sim.days_completed
    except Exception:  # noqa: BLE001 — soak đếm crash thay vì chết
        out["crashes"] += 1
        traceback.print_exc(file=sys.stderr)
        out["days_completed"] = len(out["results"])
    return out


def main(argv=None):
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=_positive_int("seed"), required=True)
    p.add_argument("--days", type=_positive_int("days"), required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
        if a.days < 1:
            raise BadInput("--days phải >= 1")
    except SystemExit:
        return 2
    except BadInput as e:
        print(f"đầu vào sai: {e}", file=sys.stderr)
        return 2
    t0 = time.perf_counter()  # chỉ đo báo cáo; không ảnh hưởng gameplay
    out = run_soak(a.seed, a.days)
    out["duration_s"] = round(time.perf_counter() - t0, 3)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
        f.write("\n")
    ok = out["crashes"] == 0 and out["days_completed"] == out["days"]
    print(f"soak seed={a.seed} days={a.days} days_completed={out['days_completed']} "
          f"crashes={out['crashes']} duration_s={out['duration_s']}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
