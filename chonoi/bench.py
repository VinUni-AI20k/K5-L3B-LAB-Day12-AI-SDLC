"""Đo bộ vẽ phần mềm của cảnh lặn bằng snapshot Gather thật."""

import argparse
from itertools import cycle
import json
import math
from pathlib import Path
import tempfile
from time import perf_counter_ns

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


WIDTH, HEIGHT = 1280, 720
SKY = bytes((207, 234, 245))
WATER_TOP = (73, 176, 220)
WATER_BOTTOM = (8, 36, 63)
DOCK = bytes((141, 110, 75))
PLANT = bytes((88, 184, 105))
PLANT_REGROWING = bytes((50, 99, 82))
FISH = bytes((246, 187, 87))
MONSTER = bytes((206, 90, 69))
DIVER = bytes((248, 238, 206))


class GatherRaster:
    """Vẽ cảnh sông lên bộ đệm RGB 1280×720 trong bộ nhớ."""

    def __init__(self, gather):
        (self.min_x, max_x), (self.min_depth, max_depth) = (
            gather["bounds"]["x"], gather["bounds"]["d"]
        )
        world_width = max_x - self.min_x
        world_depth = max_depth - self.min_depth
        self.scale = min((WIDTH - 48) / world_width, (HEIGHT - 120) / world_depth)
        self.left = (WIDTH - round(world_width * self.scale)) // 2
        water_height = max(1, round(world_depth * self.scale))
        self.surface = (HEIGHT - water_height) // 2
        rows = [SKY * WIDTH] * self.surface
        for y in range(HEIGHT - self.surface):
            depth = min(1, y / water_height)
            color = bytes(round(top + (bottom - top) * depth)
                          for top, bottom in zip(WATER_TOP, WATER_BOTTOM))
            rows.append(color * WIDTH)
        self.background = b"".join(rows)
        self.pixels = bytearray(len(self.background))
        self.dock_pos = gather["dock_pos"]

    def rect(self, pos, width, height, color):
        x = self.left + round((pos[0] - self.min_x) * self.scale) - width // 2
        y = self.surface + round((pos[1] - self.min_depth) * self.scale) - height // 2
        left, right = max(0, x), min(WIDTH, x + width)
        if left >= right:
            return
        span = color * (right - left)
        for row in range(max(0, y), min(HEIGHT, y + height)):
            offset = (row * WIDTH + left) * 3
            self.pixels[offset:offset + len(span)] = span

    def render(self, snapshot):
        self.pixels[:] = self.background
        self.rect(self.dock_pos, 44, 9, DOCK)
        for node in snapshot["nodes"]:
            self.rect(node["pos"], 19, 8, PLANT if node["ready"] else PLANT_REGROWING)
        for fish in snapshot["fish"]:
            self.rect(fish["pos"], 18, 8, FISH)
        for monster in snapshot.get("monsters", ()):
            self.rect(monster["pos"], 45, 13, MONSTER)
        self.rect(snapshot["player"]["pos"], 15, 21, DIVER)


def benchmark(seconds, seed, warmup=0.0):
    load_start = perf_counter_ns()
    contract = load_contract()
    tuning = contract["tuning"]
    session = Session("gather", tuning, {}, seed, contract_version=contract["contract_version"])
    raster = GatherRaster(tuning["gather"])
    snapshots = [session.snapshot()]
    raster.render(snapshots[0])
    load_ms = (perf_counter_ns() - load_start) / 1_000_000

    # Phát lại cùng một đường bơi trên mọi máy. Chuẩn bị snapshot trước khi đo FPS.
    tick_hz = tuning["tick_hz"]
    for movement in ((0.6, 0.8), (1.0, 0.0), (0.6, -0.8)):
        inp = InputState(movement, {}, set())
        for _ in range(3 * tick_hz):
            if session.done:
                break
            session.step(inp)
            snapshots.append(session.snapshot())

    frames = cycle(snapshots)
    if warmup > 0:  # làm nóng: vẽ nhưng không tính vào số đo
        warm_start = perf_counter_ns()
        for snapshot in frames:
            raster.render(snapshot)
            if (perf_counter_ns() - warm_start) / 1_000_000_000 >= warmup:
                break

    frame_times = []
    start = previous = perf_counter_ns()
    for snapshot in frames:
        raster.render(snapshot)
        now = perf_counter_ns()
        frame_times.append(now - previous)
        if (now - start) / 1_000_000_000 >= seconds:
            break
        previous = now

    measured_s = (now - start) / 1_000_000_000
    frames = len(frame_times)
    slow_count = (frames + 99) // 100
    slowest_ns = sum(sorted(frame_times)[-slow_count:])
    return {
        "avg_fps": frames / measured_s,
        "p1_low_fps": slow_count * 1_000_000_000 / slowest_ns,
        "frames": frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }


def write_report(path, report):
    # Thay file đích sau khi đã ghi xong JSON.
    stream = tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode="w",
                                         encoding="utf-8", newline="\n")
    temporary = Path(stream.name)
    try:
        with stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", "--seconds", dest="seconds", type=float, default=30,
                        help="số giây đo FPS, sau khi làm nóng (mặc định: 30)")
    parser.add_argument("--warmup", type=float, default=3, help="số giây làm nóng không tính vào số đo (mặc định: 3)")
    parser.add_argument("--seed", type=int, default=42, help="seed của cảnh lặn (mặc định: 42)")
    parser.add_argument("--out", type=Path, default=Path("bench.json"))
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("--duration phải là số hữu hạn lớn hơn 0")
    if not math.isfinite(args.warmup) or args.warmup < 0:
        parser.error("--warmup phải là số hữu hạn không âm")
    try:
        report = benchmark(args.seconds, args.seed, args.warmup)
        write_report(args.out, report)
    except BadInput as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.exit(1, f"lỗi ghi benchmark: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
