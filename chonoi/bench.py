"""Đo bộ vẽ phần mềm của cảnh lặn bằng snapshot Gather thật (Ticket-04: cảnh buổi sáng lặn có độ tươi, cá bơi, Cá Sấu
Năm Chèo; Út Sen đứng yên ở bến; seed 42, 1280×720, làm nóng 3 s rồi đo 30 s).

`load_ms` tính từ lúc khởi chạy (đầu module, trước các import nặng) đến khung hình đầu tiên của cảnh đo.
"""

from time import perf_counter_ns

_LAUNCH_NS = perf_counter_ns()  # mốc khởi chạy của `load_ms`

import argparse  # noqa: E402
from itertools import cycle  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402
import tempfile  # noqa: E402

from .contract import load_contract
from .errors import BadInput
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
BAR_FRESH = bytes((111, 207, 111))
BAR_SPOILED = bytes((205, 70, 60))
BAR_EMPTY = bytes((30, 40, 50))
SCENE_TICKS = 600  # số bước của cảnh được phát lại: cá bơi, Cá Sấu tuần tra, giỏ hao tươi
# Giỏ của Út Sen trong cảnh đo: độ tươi giảm dần, có cá thể ươn (dưới ngưỡng) để HUD độ tươi có việc phải vẽ.
SCENE_HOLD = (("ca_loc", 100), ("ca_linh", 85), ("bong_sung", 70), ("ca_keo", 55), ("keo_neo", 40), ("bong_dien_dien", 20))


class GatherRaster:
    """Vẽ cảnh sông lên bộ đệm RGB 1280×720 trong bộ nhớ."""

    def __init__(self, gather, freshness=None):
        self.fresh_max = freshness["initial"] if freshness else None
        self.spoiled_below = freshness["spoiled_below"] if freshness else None
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
        self.freshness_hud(snapshot.get("hold") or ())

    def freshness_hud(self, hold):
        """HUD độ tươi (v1.2): mỗi cá thể trong giỏ một thanh dài theo `fresh`, đỏ khi ươn."""
        if self.fresh_max is None:
            return
        for slot, item in enumerate(hold):
            top, left, width, height = HEIGHT - 28 - 16 * slot, 20, 160, 10
            self.fill(left - 2, top - 2, width + 4, height + 4, BAR_EMPTY)
            filled = round(width * max(0, min(1, item["fresh"] / self.fresh_max)))
            color = BAR_SPOILED if item["fresh"] < self.spoiled_below else BAR_FRESH
            self.fill(left, top, filled, height, color)

    def fill(self, x, y, width, height, color):
        left, right = max(0, x), min(WIDTH, x + width)
        if left >= right:
            return
        span = color * (right - left)
        for row in range(max(0, y), min(HEIGHT, y + height)):
            offset = (row * WIDTH + left) * 3
            self.pixels[offset:offset + len(span)] = span


def scene_scenario(tuning):
    """Cảnh đo: Út Sen đứng yên ở bến (vị trí đầu của sim), giỏ có cá thể độ tươi khác nhau; cá bơi và Cá Sấu mặc định."""
    initial = tuning["freshness"]["initial"]
    return {"hold": [{"id": f"I{n}", "kind": kind, "fresh": min(fresh, initial)}
                     for n, (kind, fresh) in enumerate(SCENE_HOLD, 1)]}


def scene_snapshots(tuning, seed, contract_version, ticks=SCENE_TICKS):
    """Snapshot của cảnh đo: Út Sen không nhận input nên đứng yên; cá, Cá Sấu và độ tươi thay đổi theo từng bước."""
    from .inputs import InputState
    session = Session("gather", tuning, scene_scenario(tuning), seed, contract_version=contract_version)
    snapshots = [session.snapshot()]
    idle = InputState((0.0, 0.0), {}, set())
    for _ in range(ticks):
        if session.done:
            break
        session.step(idle)
        snapshots.append(session.snapshot())
    return snapshots


def benchmark(seconds, seed, warmup=0.0):
    contract = load_contract()
    tuning = contract["tuning"]
    raster = GatherRaster(tuning["gather"], tuning.get("freshness"))
    snapshots = scene_snapshots(tuning, seed, contract["contract_version"])
    raster.render(snapshots[0])
    load_ms = (perf_counter_ns() - _LAUNCH_NS) / 1_000_000  # từ lúc khởi chạy đến khung hình đầu tiên

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
