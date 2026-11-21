from time import perf_counter

T_START = perf_counter()

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path

from ._chromium import browser_executable, chromium
from .contract import load_contract
from .errors import BadInput
from .live import LiveGame, LiveServer

SIZE = (1280, 720)
WARM_UP_S = 3.0


def frame_metrics(intervals, load_ms):
    if not intervals:
        raise RuntimeError("Không có đủ hai khung hình trong khoảng đo.")
    frames = len(intervals)
    elapsed = math.fsum(intervals)
    slowest_count = max(1, math.ceil(.01 * frames))
    slowest = sorted(intervals, reverse=True)[:slowest_count]
    return {
        "avg_fps": round(frames / elapsed, 2),
        "p1_low_fps": round(slowest_count / math.fsum(slowest), 2),
        "frames": frames,
        "measured_s": round(elapsed, 3),
        "load_ms": load_ms,
    }


def measure(presentations, duration, started):
    first = previous = None
    intervals = []
    for payload, now in presentations:
        if payload == "finished":
            if first is not None and now >= first + WARM_UP_S + duration:
                return frame_metrics(intervals, load_ms)
            raise RuntimeError("Buổi sáng kết thúc trước khi đo đủ thời gian.")
        if payload != "frame":
            continue
        if first is None:
            first = now
            load_ms = round((first - started) * 1000)
            start = first + WARM_UP_S
            end = start + duration
        if now > end:
            return frame_metrics(intervals, load_ms)
        if previous is not None and previous >= start and now > previous:
            intervals.append(now - previous)
        previous = now
    raise RuntimeError("Dòng khung hình đã dừng trong lúc đo.")


def run(contract, seed, duration, started):
    executable = browser_executable()
    with tempfile.TemporaryDirectory(prefix="chonoi-browser-bench-") as directory:
        scratch = Path(directory)
        game = LiveGame("gather", contract["tuning"], {}, seed, inventory_out=scratch / "inventory.json",
                        autoplay=False, contract=contract)
        server = LiveServer(game, port=0)
        server.start()
        try:
            with chromium(executable, scratch, *SIZE) as client:
                client.open_page(server.url + "?benchmark=1", *SIZE)
                return measure(client.frames(), duration, started)
        finally:
            server.stop()


def write_metrics(path, metrics):
    fd, temporary = tempfile.mkstemp(prefix=".bench-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            json.dump(metrics, output, allow_nan=False)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark the rendered Gather scene at 1280x720.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=float, default=30.0, metavar="GIAY")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration must be a finite positive number of seconds")
    try:
        contract = load_contract()
        print(f"Gather benchmark, Test Contract {contract['contract_version']}, seed {args.seed}, {args.duration:g}s", flush=True)
        metrics = run(contract, args.seed, args.duration, T_START)
        write_metrics(args.out, metrics)
    except (OSError, BadInput, RuntimeError) as error:
        print(f"Benchmark: {error}", file=sys.stderr)
        return 1
    print(json.dumps(metrics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
