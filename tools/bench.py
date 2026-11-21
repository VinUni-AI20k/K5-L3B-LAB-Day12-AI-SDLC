"""Bench render v1.3 (TICKET-04): python3 tools/bench.py --seed 42 --duration 30 --out bench.json

Chỉ dùng stdlib: mở http.server cục bộ (cổng trống) phục vụ gốc repo, chạy Chrome/Chromium headless 1280×720
tới client/bench.html?debug&novideo&seed=..&duration=..&t0=<epoch ms lúc khởi chạy>. Trang tự đo (khởi động 3 s
rồi đo `duration` s bằng requestAnimationFrame) và POST JSON về /bench-result; runner ghi --out.
Đầu ra đúng {"avg_fps","p1_low_fps","frames","measured_s","load_ms"}.
Mã thoát: 0 đạt; 1 trình duyệt lỗi / quá giờ / trang báo lỗi; 2 tham số sai hoặc không tìm thấy trình duyệt.
"""

import argparse
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms")
CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env:
        return env if os.path.exists(env) else None
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def validate(res):
    """Kiểm schema đầu ra (dùng cả trong test)."""
    if not isinstance(res, dict) or set(res) != set(KEYS):
        raise ValueError(f"bench.json phải có đúng các khóa {KEYS}, đang có {sorted(res) if isinstance(res, dict) else res!r}")
    if not isinstance(res["frames"], int) or res["frames"] <= 0:
        raise ValueError("frames phải là số nguyên > 0")
    for k in ("avg_fps", "p1_low_fps", "measured_s", "load_ms"):
        if not isinstance(res[k], (int, float)) or isinstance(res[k], bool) or res[k] < 0:
            raise ValueError(f"{k} phải là số >= 0")
    if abs(res["avg_fps"] - res["frames"] / res["measured_s"]) > 0.01:
        raise ValueError("avg_fps phải bằng frames / measured_s")
    if res["p1_low_fps"] > res["avg_fps"] + 1e-6:
        raise ValueError("p1_low_fps không thể lớn hơn avg_fps")
    return res


class _Handler(http.server.SimpleHTTPRequestHandler):
    result = None
    got = None

    def do_POST(self):
        if self.path != "/bench-result":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            type(self).result = json.loads(self.rfile.read(n))
        except ValueError as e:
            type(self).result = {"error": f"JSON hỏng: {e}"}
        self.send_response(204)
        self.end_headers()
        type(self).got.set()

    def log_message(self, *a):
        pass


def main(argv=None):
    p = argparse.ArgumentParser(prog="tools/bench.py")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", type=float, default=3.0)
    a = p.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("lỗi: --duration phải > 0\n")
        return 2
    browser = find_browser()
    if not browser:
        sys.stderr.write("lỗi: không tìm thấy Chrome/Chromium (đặt CHONOI_BROWSER=<đường dẫn> để chỉ định)\n")
        return 2
    handler = type("H", (_Handler,), {"result": None, "got": threading.Event()})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    t0 = int(time.time() * 1000)
    url = (f"http://127.0.0.1:{port}/client/bench.html?debug&novideo&seed={a.seed}"
           f"&duration={a.duration:g}&warmup={a.warmup:g}&t0={t0}")
    cmd = [browser, "--headless=new", "--window-size=1280,720", f"--user-data-dir={profile}", "--no-first-run",
           "--no-default-browser-check", "--mute-audio", "--autoplay-policy=no-user-gesture-required",
           "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
           "--disable-backgrounding-occluded-windows", "--remote-debugging-port=0", url]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = handler.got.wait(timeout=a.duration + a.warmup + 90)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        srv.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    if not ok:
        sys.stderr.write("lỗi: trang bench không gửi kết quả trong thời hạn\n")
        return 1
    res = handler.result
    if "error" in res:
        sys.stderr.write(f"lỗi trang bench: {res['error']}\n")
        return 1
    try:
        validate(res)
    except ValueError as e:
        sys.stderr.write(f"lỗi schema: {e}\n")
        return 1
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({k: res[k] for k in KEYS}, f, indent=2)
        f.write("\n")
    sys.stderr.write(f"bench: {json.dumps(res)} (browser={browser})\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
