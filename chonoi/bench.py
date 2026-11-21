"""Benchmark có render (Test Contract v1.3, Ticket-04 mục 1): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

KHUNG (Integrator): CLI, dựng cảnh đo, vòng khung hình, làm nóng 3 s, đo `duration` s, tính chỉ số, ghi JSON.
Phần VẼ do E viết trong `chonoi/bench_render.py` (lớp `Renderer`, xem docstring ở đó).

Cảnh đo: buổi sáng lõi (gather v1.3: độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định), Út Sen đứng yên ở bến
(không input), cửa sổ 1280×720. Mô phỏng bước cố định 60 tick/s theo thời gian thực; mỗi khung vẽ snapshot mới nhất.

bench.json: {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}
- frames, measured_s: số khung và số giây thực tế trong khoảng đo sau làm nóng.
- avg_fps = frames / measured_s.
- p1_low_fps: lấy max(1, ceil(0.01 × frames)) khung chậm nhất, nghịch đảo thời gian trung bình của chúng (giây).
- load_ms: mili giây từ lúc khởi chạy tới khung hình đầu tiên của cảnh đo.
Mã thoát: 0 đã ghi bench.json; 2 tham số sai; 1 không mở được cửa sổ / lỗi vẽ / lỗi ghi.
"""

LAUNCH = __import__("time").perf_counter()  # mốc "lúc khởi chạy" cho load_ms, đặt trước mọi import nặng

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

WIDTH, HEIGHT = 1280, 720
WARMUP_S = 3.0
SIM_DT = 1.0 / 60.0
MAX_STEPS_PER_FRAME = 5  # khung quá chậm thì không đuổi theo quá 5 bước mô phỏng


def compute_metrics(frame_times, measured_s, load_ms) -> dict:
    """Chỉ số theo Ticket-04 từ thời gian từng khung (giây) trong khoảng đo."""
    frames = len(frame_times)
    if frames == 0 or measured_s <= 0:
        return {"avg_fps": 0.0, "p1_low_fps": 0.0, "frames": frames, "measured_s": round(measured_s, 3),
                "load_ms": round(load_ms)}
    n = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_times, reverse=True)[:n]
    avg_slow = sum(slowest) / n
    return {
        "avg_fps": round(frames / measured_s, 2),
        "p1_low_fps": round(1.0 / avg_slow, 2) if avg_slow > 0 else 0.0,
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": round(load_ms),
    }


def load_renderer():
    from .bench_render import Renderer  # E viết
    return Renderer()


def run(seed, duration, renderer=None, warmup=WARMUP_S, contract=None, launch=LAUNCH, clock=time.perf_counter):
    """Chạy cảnh đo và trả dict chỉ số. `renderer` cần open(w, h), draw(snapshot) -> bool, close().
    draw trả False khi người dùng đóng cửa sổ (dừng sớm)."""
    contract = contract or load_contract()
    sess = Session("gather", contract["tuning"], {}, seed)  # gather lõi mặc định, Út Sen ở bến
    idle = InputState((0.0, 0.0), {}, set())
    renderer = renderer or load_renderer()
    renderer.open(WIDTH, HEIGHT)
    try:
        acc, load_ms = 0.0, None
        t_prev = clock()
        start = t_prev
        measure_start, frame_times = None, []
        while True:
            now = clock()
            acc += now - t_prev
            steps = 0
            while acc >= SIM_DT and steps < MAX_STEPS_PER_FRAME and not sess.done:
                sess.step(idle)
                acc -= SIM_DT
                steps += 1
            if steps == MAX_STEPS_PER_FRAME:
                acc = 0.0
            if renderer.draw(sess.snapshot()) is False:
                break
            t_end = clock()
            if load_ms is None:
                load_ms = (t_end - launch) * 1000.0
            if measure_start is None:
                if t_end - start >= warmup:
                    measure_start = t_end  # khung đo đầu tiên tính từ đây
            else:
                frame_times.append(t_end - t_prev_end)
            t_prev_end = t_end  # cập nhật TRƯỚC khi dừng để measured_s khớp đúng các khung đã đếm
            t_prev = now
            if measure_start is not None and t_end - measure_start >= duration:
                break
        measured = (t_prev_end - measure_start) if measure_start is not None else 0.0
    finally:
        renderer.close()
    return compute_metrics(frame_times, measured, load_ms or 0.0)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.bench")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--duration", required=True, type=float)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if not (a.duration > 0 and math.isfinite(a.duration)):
        sys.stderr.write("lỗi: --duration phải là số giây dương\n")
        return 2
    try:
        contract = load_contract()
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        result = run(a.seed, a.duration, contract=contract)
    except Exception as e:  # không mở được cửa sổ (không có display), lỗi vẽ...
        sys.stderr.write(f"lỗi benchmark: {type(e).__name__}: {e}\n")
        return 1
    try:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
