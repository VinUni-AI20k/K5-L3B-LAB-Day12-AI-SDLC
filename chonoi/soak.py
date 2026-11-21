"""Deterministic multi-day headless soak runner (TICKET-04)."""

import argparse
import json
import sys
import time

from .contract import load_contract
from .day import DaySession
from .errors import BadInput
from .inputs import InputState
from .runner import score_of


def run_soak(seed: int, days: int) -> dict:
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise BadInput("--days phải là số nguyên dương")

    started = time.perf_counter()
    tuning = load_contract()["tuning"]
    session = DaySession(tuning, {}, seed, days)
    results = []

    while not session.done:
        at_dock = session.sim.phase == "gather" and session.phase_tick == 0
        inp = InputState((0.0, 0.0), {}, {"interact"} if at_dock else set())
        rows = session.step(inp)
        for row in rows:
            if row["name"] == "shop_end":
                results.append({
                    "day": row["day"],
                    "earned": session.earned,
                    "reputation": session.reputation,
                    "score": score_of(tuning, session.earned, session.reputation),
                })

    return {
        "days": days,
        "days_completed": session.days_completed,
        "crashes": 0 if session.reason == "days_complete" else 1,
        "results": results,
        "duration_s": round(time.perf_counter() - started, 6),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chonoi.soak")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--days", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        report = run_soak(args.seed, args.days)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except BadInput as exc:
        sys.stderr.write(f"đầu vào sai: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"lỗi ghi: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
