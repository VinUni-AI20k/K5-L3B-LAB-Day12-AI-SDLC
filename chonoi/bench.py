"""Phase 4 (M5.1) — Benchmark cảnh lặn `chonoi.bench` (Ticket04 / Test Contract v1.3).

Cách chạy:
    python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json

Đo hiệu năng cảnh buổi sáng lõi (1280×720, làm nóng 3 s + đo `duration` s, Út Sen đứng yên ở bến,
cá bơi và render frame snapshot), xuất đúng 5 trường JSON:
    {"avg_fps": ..., "p1_low_fps": ..., "frames": ..., "measured_s": ..., "load_ms": ...}
"""

import argparse
import json
import math
import os
import sys
import time

from .contract import load_contract
from .inputs import InputState
from .runner import Session

IDLE_INPUT = InputState((0.0, 0.0), {"interact": False, "catch": False}, set())
TARGET_FRAME_S = 1.0 / 60.0


def _render_frame_workload(snap: dict, width: int = 1280, height: int = 720) -> int:
    """Mô phỏng công việc dựng khung hình 1280×720 từ snapshot (tính tọa độ camera, culling, JSON serialize)."""
    p = snap.get("player") or {}
    px, pd = p.get("pos", [2.0, 0.0])
    scale = min(width / 46.0, (height - 126) / 20.0) * 1.25
    drawn = 0
    for n in snap.get("nodes", ()):
        nx, nd = n["pos"]
        sx = width * 0.5 + (nx - px) * scale
        sy = height * 0.5 + (nd - pd) * scale
        if -64 <= sx <= width + 64 and -64 <= sy <= height + 64:
            drawn += 1
    for f in snap.get("fish", ()):
        fx, fd = f["pos"]
        sx = width * 0.5 + (fx - px) * scale
        sy = height * 0.5 + (fd - pd) * scale
        if -64 <= sx <= width + 64 and -64 <= sy <= height + 64:
            drawn += 1
    for m in snap.get("monsters", ()):
        mx, md = m["pos"]
        sx = width * 0.5 + (mx - px) * scale
        sy = height * 0.5 + (md - pd) * scale
        if -64 <= sx <= width + 64 and -64 <= sy <= height + 64:
            drawn += 1
    _ = json.dumps(snap, separators=(",", ":"))
    return drawn


def run_benchmark(seed: int = 42, duration: float = 30.0, warmup: float = 3.0) -> dict:
    t_load_start = time.perf_counter()
    tuning = load_contract()["tuning"]
    session = Session("gather", tuning, {}, seed)
    _render_frame_workload(session.snapshot())
    load_ms = round((time.perf_counter() - t_load_start) * 1000.0, 2)

    # Làm nóng (warmup)
    t_warm_end = time.perf_counter() + max(0.0, float(warmup))
    while time.perf_counter() < t_warm_end:
        if session.done:
            session = Session("gather", tuning, {}, seed)
        session.step(IDLE_INPUT)
        _render_frame_workload(session.snapshot())

    # Đo chính thức trong `duration` giây (tốc độ khung hình thực, không sleep nhân tạo)
    frame_times = []
    t_start = time.perf_counter()
    t_end = t_start + max(0.05, float(duration))
    while True:
        f0 = time.perf_counter()
        if f0 >= t_end:
            break
        if session.done:
            session = Session("gather", tuning, {}, seed)
        session.step(IDLE_INPUT)
        _render_frame_workload(session.snapshot())
        f1 = time.perf_counter()
        frame_times.append(max(1e-6, f1 - f0))

    measured_s = max(1e-6, time.perf_counter() - t_start)
    frames = len(frame_times)
    avg_fps = frames / measured_s

    # p1_low_fps: chọn max(1, ceil(0.01 * frames)) khung chậm nhất rồi lấy nghịch đảo thời gian trung bình
    slow_n = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_times, reverse=True)[:slow_n]
    avg_slow_s = sum(slowest) / len(slowest)
    p1_low_fps = 1.0 / avg_slow_s

    return {
        "avg_fps": round(avg_fps, 2),
        "p1_low_fps": round(p1_low_fps, 2),
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": load_ms,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark cảnh lặn 1280x720 (Contract v1.3).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--warmup", type=float, default=3.0)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.duration <= 0 or a.warmup < 0:
        sys.stderr.write("duration phải > 0 và warmup >= 0\n")
        return 2
    res = run_benchmark(seed=a.seed, duration=a.duration, warmup=a.warmup)
    parent = os.path.dirname(os.path.abspath(a.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
