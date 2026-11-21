"""Benchmark cảnh lặn (Test Contract v1.3, TICKET-04 mục 1).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (độ tươi v1.2, cá bơi/sinh, Cá Sấu Năm Chèo), Út Sen đứng yên ở bến, seed 42.
Làm nóng 3 s rồi đo `--duration` giây.

Một "khung hình" = đúng việc cửa sổ chơi (`chonoi.live`) làm mỗi khung ở 60 Hz phía máy: một bước mô phỏng,
dựng snapshot và mã hóa JSON trạng thái mà client vẽ (`GET /state`). Vòng chạy giữ nhịp 60 Hz như cửa sổ thật.
GIỚI HẠN: phần vẽ canvas 1280×720 chạy trong trình duyệt nên không đo ở đây (ghi trong Release notes).

Đầu ra: {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}
  avg_fps    = frames / measured_s
  p1_low_fps = 1 / trung bình thời gian của max(1, ceil(0.01 × frames)) khung chậm nhất (giây)
  load_ms    = từ lúc khởi chạy tới khung hình đầu tiên của cảnh đo
"""

import argparse
import json
import math
import sys
import time

T_START = time.perf_counter()  # "lúc khởi chạy" của tiến trình bench

from .contract import load_contract  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

WARMUP_S = 3.0
FRAME_S = 1.0 / 60.0
IDLE = InputState((0.0, 0.0), {}, set())


def frame(sess, tuning):
    """Một khung: bước mô phỏng + snapshot + JSON như GET /state của cửa sổ chơi."""
    if sess.done:  # hết ca trong lúc đo -> dựng lại cảnh (không xảy ra với 33 s < 180 s ca)
        sess.__init__("gather", tuning, {}, sess._seed)
    sess.step(IDLE)
    snap = sess.snapshot()
    snap["meta"] = dict(tuning["gather"], freshness=tuning.get("freshness"))
    return json.dumps(snap, ensure_ascii=False, separators=(",", ":"))


def run_bench(seed: int, duration: float) -> dict:
    tuning = load_contract()["tuning"]
    sess = Session("gather", tuning, {}, seed)  # bến = start_pos, không input -> đứng yên ở bến
    sess._seed = seed
    frame(sess, tuning)
    load_ms = (time.perf_counter() - T_START) * 1000.0
    # làm nóng
    nxt = time.perf_counter()
    end_warm = nxt + WARMUP_S
    while time.perf_counter() < end_warm:
        frame(sess, tuning)
        nxt += FRAME_S
        delay = nxt - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
    # đo
    times = []
    start = last = time.perf_counter()
    stop = start + duration
    nxt = start
    while True:
        frame(sess, tuning)
        nxt += FRAME_S
        delay = nxt - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        now = time.perf_counter()
        times.append(now - last)
        last = now
        if now >= stop:
            break
    measured = last - start
    n = len(times)
    k = max(1, math.ceil(0.01 * n))
    slow = sorted(times, reverse=True)[:k]
    return {"avg_fps": round(n / measured, 2), "p1_low_fps": round(1.0 / (sum(slow) / k), 2),
            "frames": n, "measured_s": round(measured, 3), "load_ms": round(load_ms, 1)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if not (a.duration > 0):
        sys.stderr.write("đầu vào sai: --duration phải > 0\n")
        return 2
    report = run_bench(a.seed, a.duration)
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
