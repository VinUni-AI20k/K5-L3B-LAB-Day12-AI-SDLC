"""Benchmark có render (TICKET-04 mục 1): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (contract v1.3 / gameplay v1.2) với độ tươi, cá bơi, Cá Sấu Năm Chèo và hiệu ứng mặc định
(sóng mặt nước); Út Sen đứng yên ở bến (không input). Mô phỏng chạy CÙNG lớp sim với headless (`runner.Session`)
theo bước cố định 60 tick/s; mỗi khung hình RENDER toàn cảnh vào framebuffer RGB 1280×720 (rasterizer phần mềm
thuần Python — client chơi thật vẽ bằng canvas trên trình duyệt nên bench không mở cửa sổ; xem release notes).
Làm nóng 3 s (không tính), sau đó đo `--duration` giây.

Xuất 5 trường: avg_fps = frames / measured_s; p1_low_fps = 1 / trung bình thời gian của max(1, ceil(0.01 × frames))
khung chậm nhất (giây); frames, measured_s trong khoảng đo; load_ms = từ lúc khởi chạy module tới khung đầu tiên
của cảnh đo. `--frame-out <file.ppm>` lưu khung cuối làm bằng chứng render.
"""

import time

_T0 = time.perf_counter()  # mốc "khởi chạy" (sau khi trình thông dịch nạp module này)

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402

from .contract import load_contract  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

W, H = 1280, 720
TICK_S = 1.0 / 60.0
MAX_STEPS_PER_FRAME = 5
IDLE = InputState((0.0, 0.0), {}, set())
KIND_RGB = {"ca_loc": (124, 154, 82), "ca_linh": (214, 230, 242), "ca_keo": (217, 160, 102),
            "bong_dien_dien": (242, 194, 48), "bong_sung": (232, 121, 156), "keo_neo": (143, 207, 107)}


class Frame:
    """Framebuffer RGB 1280×720; vẽ bằng gán lát theo hàng (nhanh trong Python thuần)."""

    def __init__(self, background: bytes):
        self.bg = background
        self.px = bytearray(background)

    def clear(self):
        self.px[:] = self.bg

    def rect(self, x0, y0, x1, y1, rgb):
        x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(rgb) * (x1 - x0)
        n = len(row)
        for y in range(y0, y1):
            o = (y * W + x0) * 3
            self.px[o:o + n] = row

    def ellipse(self, cx, cy, rx, ry, rgb):
        rx, ry = max(1, int(rx)), max(1, int(ry))
        for dy in range(-ry, ry + 1):
            half = int(rx * math.sqrt(max(0.0, 1 - (dy / ry) ** 2)))
            self.rect(cx - half, cy + dy, cx + half + 1, cy + dy + 1, rgb)

    def ppm(self) -> bytes:
        return b"P6\n%d %d\n255\n" % (W, H) + bytes(self.px)


class Scene:
    """Cảnh lặn 1280×720: trời, nước gradient theo độ sâu, bến, nút hái, cá, quái, Út Sen, HUD (oxy, Máu, giỏ + độ tươi)."""

    TOP, BOTTOM, SKY = 110, 70, 6

    def __init__(self, tuning):
        g = tuning["gather"]
        self.X, self.D = g["bounds"]["x"][1], g["bounds"]["d"][1]
        self.s = min((W - 20) / (self.X + 4), (H - self.TOP - self.BOTTOM) / (self.D + self.SKY + 1))
        self.ox = (W - self.s * (self.X + 4)) / 2 + 2 * self.s
        self.oy = self.TOP + self.SKY * self.s
        self.below = tuning["freshness"]["spoiled_below"]
        rows = []
        for y in range(H):
            if y < self.TOP:
                c = (16, 22, 28)
            elif y < self.oy:
                c = (207, 234, 245)
            elif y < self.sy(self.D):
                t = (y - self.oy) / max(1, self.sy(self.D) - self.oy)
                c = (int(73 - 65 * t), int(176 - 140 * t), int(220 - 157 * t))
            else:
                c = (46, 31, 16)
            rows.append(bytes(c) * W)
        self.frame = Frame(b"".join(rows))

    def sx(self, x):
        return self.ox + x * self.s

    def sy(self, d):
        return self.oy + d * self.s

    def draw(self, snap, t):
        f, s = self.frame, self.s
        f.clear()
        # hiệu ứng mặc định: sóng lăn tăn trên mặt nước
        for k in range(0, W, 48):
            off = int(6 * math.sin(t * 2.0 + k * 0.05))
            f.rect(k + off, self.oy - 2, k + off + 24, self.oy + 2, (233, 247, 255))
        dp = snap.get("dock_pos") or [2, 0]
        f.rect(self.sx(dp[0] - 1.5), self.sy(-0.7), self.sx(dp[0] + 1.5), self.sy(0.2), (141, 110, 75))
        for n in snap["nodes"]:
            c = KIND_RGB.get(n["kind"], (190, 190, 190)) if n["ready"] else (90, 120, 130)
            f.ellipse(self.sx(n["pos"][0]), self.sy(n["pos"][1]), 0.9 * s, 0.4 * s, c)
        for fi in snap["fish"]:
            f.ellipse(self.sx(fi["pos"][0]), self.sy(fi["pos"][1]), 0.9 * s, 0.45 * s, KIND_RGB.get(fi["kind"], (200, 200, 200)))
        for m in snap.get("monsters", []):
            f.ellipse(self.sx(m["pos"][0]), self.sy(m["pos"][1]), 1.1 * s, 0.5 * s, (156, 92, 194))
        p = snap["player"]
        f.ellipse(self.sx(p["pos"][0]), self.sy(p["pos"][1]), 0.6 * s, 0.6 * s, (255, 138, 61))
        # HUD: panel, thanh oxy, Máu, giỏ với màu độ tươi (đỏ = ươn)
        f.rect(12, 10, W - 12, self.TOP - 10, (13, 25, 32))
        oxy = p["oxygen_ticks"] / max(1, p["oxygen_max_ticks"])
        f.rect(180, 30, 380, 56, (0, 0, 0))
        f.rect(180, 30, 180 + int(200 * oxy), 56, (239, 83, 80) if oxy < 0.25 else (69, 196, 223))
        for i in range(p["hp_max"]):
            f.rect(400 + i * 30, 30, 424 + i * 30, 54, (255, 112, 133) if i < p["hp"] else (80, 40, 50))
        for i in range(snap["hold_capacity"]):
            x0 = 520 + i * 34
            f.rect(x0, 30, x0 + 28, 58, (60, 70, 78))
            if i < len(snap["hold"]):
                it = snap["hold"][i]
                fr = it["fresh"] / 100.0
                c = (220, 60, 60) if it["fresh"] < self.below else (int(255 * (1 - fr)), int(200 * fr + 40), 90)
                f.rect(x0 + 3, 33, x0 + 25, 55, c)
                f.rect(x0 + 3, 60, x0 + 3 + int(22 * fr), 66, KIND_RGB.get(it["kind"], (200, 200, 200)))


def run_bench(seed, duration, warmup=3.0, frame_out=None):
    tuning = load_contract()["tuning"]
    sess = Session("gather", tuning, {}, seed)  # cảnh lõi mặc định: 8 đàn cá bơi, M1, độ tươi; Út Sen ở bến
    scene = Scene(tuning)
    snap = sess.snapshot()
    snap["dock_pos"] = tuning["gather"]["dock_pos"]
    start = time.perf_counter()
    scene.draw(snap, 0.0)  # khung hình đầu tiên của cảnh đo
    load_ms = (time.perf_counter() - _T0) * 1000.0
    acc, last = 0.0, time.perf_counter()
    measuring, m_start, times = False, None, []
    while True:
        now = time.perf_counter()
        dt, last = now - last, now
        acc += dt
        steps = 0
        while acc >= TICK_S and steps < MAX_STEPS_PER_FRAME and not sess.done:
            sess.step(IDLE)
            acc -= TICK_S
            steps += 1
        if steps == MAX_STEPS_PER_FRAME:
            acc = 0.0  # không đuổi theo vô hạn khi máy chậm
        snap = sess.snapshot()
        snap["dock_pos"] = tuning["gather"]["dock_pos"]
        scene.draw(snap, now - start)
        end = time.perf_counter()
        if not measuring and end - start >= warmup:
            measuring, m_start, prev = True, end, end
            continue
        if measuring:
            times.append(end - prev)
            prev = end
            if end - m_start >= duration:
                break
    measured_s = round(prev - m_start, 4)  # avg_fps tính từ đúng giá trị xuất ra -> frames / measured_s khớp
    frames = len(times)
    k = max(1, math.ceil(0.01 * frames))
    slow = sorted(times, reverse=True)[:k]
    result = {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(1.0 / (sum(slow) / len(slow)), 2),
              "frames": frames, "measured_s": measured_s, "load_ms": int(round(load_ms))}
    if frame_out:
        with open(frame_out, "wb") as fh:
            fh.write(scene.frame.ppm())
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark có render cảnh lặn (TICKET-04).")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--duration", type=float, required=True, help="giây đo sau làm nóng")
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=float, default=3.0, help="giây làm nóng (mặc định 3 theo đề)")
    ap.add_argument("--frame-out", dest="frame_out", help="lưu khung cuối dạng PPM (bằng chứng render)")
    a = ap.parse_args(argv)
    if a.duration <= 0 or a.warmup < 0:
        sys.stderr.write("đầu vào sai: --duration phải > 0, --warmup >= 0\n")
        return 2
    res = run_bench(a.seed, a.duration, a.warmup, a.frame_out)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh)
        fh.write("\n")
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
