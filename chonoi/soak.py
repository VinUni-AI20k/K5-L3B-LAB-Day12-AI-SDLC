"""P4-M4.1 / M2.1 — Soak headless 10 Ngày liên tục (`python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`).

Chạy N Ngày liên tục trong 1 tiến trình headless bằng bot tất định (D1–D5 lặp cho D6–D10),
xuất JSON gồm: days, days_completed, crashes, results[] ({day, earned, reputation, score}), duration_s.
"""

import argparse
import json
import os
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


def _bot_input(sess: Session) -> InputState:
    """Bot tất định gọn: ở gather cập bến sớm (sau 1 bước), ở quan chờ hết ca, ở shop mua nâng cấp rồi shop_done."""
    sim = sess.sim
    phase = sim.phase
    if phase == "gather":
        # Xuất phát ngay tại bến [2, 0] -> cập bến ở phase_tick == 0 để chạy nhanh & tất định qua 10 ngày
        if sim.phase_tick == 0:
            return InputState((0.0, 0.0), {"interact": True}, {"interact"})
        return InputState((0.0, 0.0), {}, set())
    if phase == "shop":
        # Thử mua oxygen/hp nếu đủ tiền, rồi kết thúc Shop ngay
        buy = None
        for upg in ("oxygen", "hp"):
            levels = sess.tuning.get("shop", {}).get("upgrades", {}).get(upg, [])
            cur = int(sim.upgrades.get(upg, 0))
            nxt = next((lv for lv in levels if lv["level"] == cur + 1), None)
            if nxt is not None and sim.money >= int(nxt["price"]):
                buy = upg
                break
        return InputState((0.0, 0.0), {"shop_done": True}, {"shop_done"}, buy=buy)
    return InputState((0.0, 0.0), {}, set())


def run_soak(seed: int, days: int, out_path: str) -> dict:
    t0 = time.perf_counter()
    tuning = load_contract()["tuning"]
    results = []
    crashes = 0
    days_completed = 0
    try:
        sess = Session("day", tuning, {}, seed=seed, days=days)
        max_ticks = days * 25000
        while not sess.done and sess.tick < max_ticks:
            evs = sess.step(_bot_input(sess))
            for ev in evs:
                if ev["name"] == "shop_end":
                    snap = sess.snapshot()
                    results.append({
                        "day": ev.get("day", len(results) + 1),
                        "earned": int(snap["earned"]),
                        "reputation": round(float(snap["reputation"]), 3),
                        "score": int(snap["score"]),
                    })
        days_completed = int(sess.sim.days_completed)
    except Exception:
        crashes += 1
        raise
    duration_s = round(time.perf_counter() - t0, 3)
    payload = {
        "days": int(days),
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return payload


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--days", required=True, type=int)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("lỗi: --days phải >= 1\n")
        return 2
    try:
        run_soak(a.seed, a.days, a.out)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
