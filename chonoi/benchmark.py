"""Headless gather-scene throughput benchmark.

Run: python3 -m chonoi.benchmark --seed 42 --duration 30 --out bench.json
"""

import argparse
import json
import math
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputPlayer
from .runner import Session
from .scenario import load_scenario


def benchmark(seed, duration):
    load_start = time.perf_counter()
    contract = load_contract()
    tuning = contract["tuning"]
    scenario = load_scenario(None, "gather", tuning)
    session = Session("gather", tuning, scenario, seed)
    player = InputPlayer([])
    load_ms = (time.perf_counter() - load_start) * 1000

    start = time.perf_counter()
    bucket_start = start
    bucket_frames = 0
    frames = 0
    windows = []
    while time.perf_counter() - start < duration:
        session.step(player.advance(session.tick))
        frames += 1
        bucket_frames += 1
        now = time.perf_counter()
        elapsed = now - bucket_start
        if elapsed >= 0.25:
            windows.append(bucket_frames / elapsed)
            bucket_start = now
            bucket_frames = 0
        if session.done:
            session = Session("gather", tuning, scenario, seed)
            player = InputPlayer([])
    finish = time.perf_counter()
    measured_s = finish - start
    if bucket_frames:
        windows.append(bucket_frames / max(finish - bucket_start, 1e-9))
    low_index = max(0, math.ceil(len(windows) * 0.01) - 1)
    p1_low_fps = sorted(windows)[low_index] if windows else 0
    return {
        "avg_fps": frames / measured_s if measured_s else 0,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="chonoi.benchmark")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration phải là số hữu hạn > 0")
    try:
        result = benchmark(args.seed, args.duration)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except (BadInput, OSError) as exc:
        sys.stderr.write(f"benchmark lỗi: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
