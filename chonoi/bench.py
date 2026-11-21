"""Benchmark CÓ RENDER (Phase4.md mục 1): đo FPS thật của cảnh lặn trong trình duyệt.

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng (`gather`) với luật hiện hành (độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định), Út Sen đứng yên ở bến,
cửa sổ 1280×720. Làm nóng 3 s rồi đo `--duration` giây. Cách chạy: khởi động máy chủ chơi trực tiếp (`chonoi.live`),
mở Chrome/Chromium không đầu (headless) tới `/?bench=3,<duration>`; trang ghi thời gian từng khung hình (requestAnimationFrame)
và gửi về `/bench/result`. Lệnh này tính 5 trường theo ticket:

    frames, measured_s   số khung và số giây thực tế trong khoảng đo (sau làm nóng)
    avg_fps              frames / measured_s
    p1_low_fps           lấy max(1, ceil(0.01 × frames)) khung chậm nhất, trung bình thời gian rồi lấy nghịch đảo (giây)
    load_ms              mili giây từ lúc khởi chạy trình duyệt đến khung hình đầu tiên của cảnh đo

Yêu cầu: có Chrome / Chromium / Edge (đặt biến môi trường CHROME_BIN để chỉ đường dẫn). Chỉ dùng thư viện chuẩn Python.
Mã thoát: 0 xong; 2 tham số sai; 1 không chạy được trình duyệt hoặc quá thời gian.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer

from .contract import load_contract
from .live import MAX_BODY, LiveGame, _Handler

WARMUP_S = 3.0
WINDOW = (1280, 720)


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):  # trình duyệt bị tắt khi còn kết nối mở: không in traceback
        pass


class _BenchState:
    def __init__(self):
        self.started_at = None      # perf_counter lúc trang vẽ khung đầu tiên của cảnh
        self.durations_ms = None    # danh sách thời gian từng khung hình trong khoảng đo
        self.done = threading.Event()


class _BenchHandler(_Handler):
    state: _BenchState = None

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/bench/start", "/bench/result"):
            return super().do_POST()
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if 0 < n <= 4 * MAX_BODY * 64 else b""
        if path == "/bench/start":
            if self.state.started_at is None:
                self.state.started_at = time.perf_counter()
        else:
            try:
                self.state.durations_ms = [float(x) for x in json.loads(raw.decode("utf-8"))["durations_ms"]]
            except (ValueError, KeyError, TypeError):
                self._send(400, b'{"error":"body sai"}')
                return
            self.state.done.set()
        self._send(200, b'{"ok":true}')


def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    if sys.platform == "darwin":
        cands = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    elif sys.platform.startswith("win"):
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA") if os.environ.get(k)]
        cands = [os.path.join(r, *rest) for r in roots for rest in
                 (("Google", "Chrome", "Application", "chrome.exe"), ("Microsoft", "Edge", "Application", "msedge.exe"))]
    else:
        cands = []
    for c in cands:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    return None


def compute(durations_ms, load_ms):
    """5 trường của bench.json từ thời gian từng khung hình (mili giây)."""
    frames = len(durations_ms)
    measured_s = sum(durations_ms) / 1000.0
    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(durations_ms, reverse=True)[:k]
    p1_low = 1000.0 / (sum(slowest) / len(slowest))
    return {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(p1_low, 2), "frames": frames,
            "measured_s": round(measured_s, 3), "load_ms": int(round(load_ms))}


def _kill(proc):
    try:
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        else:
            proc.terminate()
            proc.wait(timeout=5)
    except Exception:  # noqa: BLE001 - dọn dẹp, không làm hỏng kết quả
        pass


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark có render (Phase4.md)")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True, help="số giây đo (sau 3 s làm nóng)")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("lỗi: --duration phải > 0\n")
        return 2
    chrome = find_chrome()
    if not chrome:
        sys.stderr.write("không tìm thấy Chrome/Chromium/Edge (đặt biến môi trường CHROME_BIN)\n")
        return 1

    tuning = load_contract()["tuning"]
    game = LiveGame("gather", tuning, {}, a.seed)        # cảnh chuẩn: buổi sáng, không input (Út Sen đứng yên ở bến)
    state = _BenchState()
    handler = type("H", (_BenchHandler,), {"game": game, "state": state})
    httpd = _QuietServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    game.start()

    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    url = f"http://127.0.0.1:{port}/?bench={WARMUP_S:g},{a.duration:g}"
    cmd = [chrome, "--headless=new", "--hide-scrollbars", f"--window-size={WINDOW[0]},{WINDOW[1]}",
           f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
           "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
           "--disable-backgrounding-occluded-windows", url]
    t_launch = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rc = 0
    try:
        if not state.done.wait(timeout=WARMUP_S + a.duration + 90):
            sys.stderr.write("quá thời gian chờ kết quả từ trình duyệt\n")
            rc = 1
        elif not state.durations_ms or state.started_at is None:
            sys.stderr.write("trình duyệt không gửi đủ dữ liệu\n")
            rc = 1
        else:
            result = compute(state.durations_ms, (state.started_at - t_launch) * 1000.0)
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")
            print(json.dumps(result), flush=True)
    finally:
        _kill(proc)
        game.stop()
        httpd.shutdown()
        httpd.server_close()
        shutil.rmtree(profile, ignore_errors=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
