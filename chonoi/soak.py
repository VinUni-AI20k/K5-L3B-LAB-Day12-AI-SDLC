"""Deterministic multi-day headless soak runner.

Run: python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
"""

import argparse
import json
import math
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session
from .scenario import load_scenario


def soak(seed, days):
    started = time.perf_counter()
    contract = load_contract()
    tuning = contract["tuning"]
    scenario = load_scenario(None, "day", tuning)
    session = Session("day", tuning, scenario, seed, days=days)
    results = []
    crashes = 0
    neutral = InputState((0.0, 0.0), {}, set())
    shop_done = InputState((0.0, 0.0), {}, {"shop_done"})
    try:
        while not session.done:
            inp = shop_done if session.sim.phase == "shop" else neutral
            rows = session.step(inp)
            for row in rows:
                if row["type"] == "event" and row["name"] == "shop_end":
                    results.append({
                        "day": row["day"],
                        "earned": session.sim.earned,
                        "reputation": session.sim.reputation,
                        "score": (session.sim.earned + tuning["score"]["reputation_multiplier"]
                                  * math.floor(session.sim.reputation)),
                    })
    except Exception as exc:  # Report a crash in the artifact so the soak fails visibly.
        crashes += 1
        sys.stderr.write(f"soak crash: {type(exc).__name__}: {exc}\n")
    return {
        "days": days,
        "days_completed": session.sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": time.perf_counter() - started,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="chonoi.soak")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--days", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.days <= 10:
        parser.error("--days phải trong [1, 10]")
    try:
        result = soak(args.seed, args.days)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except (BadInput, OSError) as exc:
        sys.stderr.write(f"soak lỗi: {exc}\n")
        return 1
    return 0 if result["days_completed"] == args.days and result["crashes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
