"""Ticket-04 AC-P4-02: benchmark *render thật* của cảnh Gather trong trình duyệt.

Chạy: python -m chonoi.bench --seed 42 --duration 30 --out bench.json
Không có trình duyệt / không nhận được mẫu rAF => mã 1, KHÔNG tạo số FPS giả.
Không đổi tick, JSONL hoặc cơ chế mô phỏng; dùng chính LiveGame/LiveServer.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time
import webbrowser

from .contract import load_contract
from .errors import BadInput
from .live import LiveGame, LiveServer, _Handler


class BenchRun:
    """Kết quả gửi từ requestAnimationFrame, tính toán cuối cùng ở Python."""

    def __init__(self, started, expected_duration=None):
        self.started = started
        self.expected_duration = expected_duration
        self.first_frame = None
        self.data = None
        self.error = None
        self.done = threading.Event()
        self._lock = threading.Lock()

    def fail(self, message):
        with self._lock:
            if self.data is not None or self.error is not None:
                raise ValueError("benchmark đã kết thúc")
            if not isinstance(message, str) or not 1 <= len(message) <= 200:
                raise ValueError("thông báo lỗi benchmark không hợp lệ")
            self.error = message
            self.done.set()

    def mark_first_frame(self):
        with self._lock:
            if self.first_frame is None:
                self.first_frame = time.perf_counter()

    def submit(self, obj):
        if not isinstance(obj, dict) or set(obj) != {"frame_intervals_ms"}:
            raise ValueError("yêu cầu frame_intervals_ms")
        samples = obj["frame_intervals_ms"]
        if not isinstance(samples, list) or not 1 <= len(samples) <= 60000:
            raise ValueError("frame_intervals_ms phải là danh sách không rỗng (tối đa 60000)")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
               not math.isfinite(v) or v <= 0 or v > 60000 for v in samples):
            raise ValueError("thời gian từng khung hình phải dương và hữu hạn (ms)")
        with self._lock:
            if self.first_frame is None:
                raise ValueError("chưa nhận khung hình đầu tiên của cảnh Gather")
            if self.data is not None or self.error is not None:
                raise ValueError("một lượt chỉ được gửi một kết quả")
            elapsed_ms = math.fsum(samples)
            if self.expected_duration is not None:
                if elapsed_ms + 1 < self.expected_duration * 1000:
                    raise ValueError("chưa đo đủ khoảng thời gian yêu cầu")
                # Khung hinh gap khi tab bi throttling khong phai mot luot do 30 giay lien tuc.
                # Cho phep sai so toi da 1s do khung hinh cuoi va scheduling.
                if elapsed_ms > self.expected_duration * 1000 + 1000:
                    raise ValueError("thời gian đo vượt quá giới hạn: tab có thể bị gián đoạn")
                if time.perf_counter() - self.first_frame < 3 + self.expected_duration - 0.5:
                    raise ValueError("chưa đủ 3 giây làm nóng và thời gian đo")
            frames = len(samples)
            slow_count = max(1, math.ceil(frames * 0.01))
            slowest_ms = math.fsum(sorted(samples, reverse=True)[:slow_count])
            self.data = {
                "avg_fps": frames * 1000 / elapsed_ms,
                "p1_low_fps": slow_count * 1000 / slowest_ms,
                "frames": frames,
                "measured_s": elapsed_ms / 1000,
                "load_ms": round((self.first_frame - self.started) * 1000, 3),
            }
            return self.data


class BenchHandler(_Handler):
    """Giữ nguyên LiveServer; chỉ thêm hai endpoint dành cho benchmark."""

    bench_run = None

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/bench-start", "/bench", "/bench-error"):
            return super().do_POST()
        if self.headers.get("Origin") not in (None, f"http://{self.server.server_address[0]}:{self.server.server_address[1]}"):
            self._send(403, b'{"error":"origin khong hop le"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        # 60k khung x số millis = < 1 MiB. Chặn request quá lớn.
        if not 0 <= length <= 1024 * 1024:
            self._send(400, b'{"error":"body qua lon"}')
            return
        try:
            raw = self.rfile.read(length)
            obj = json.loads(raw.decode("utf-8"))
            if path == "/bench-start":
                if obj != {}:
                    raise ValueError("bench-start chỉ chấp nhận object rỗng")
                self.bench_run.mark_first_frame()
            elif path == "/bench-error":
                if not isinstance(obj, dict) or set(obj) != {"error"}:
                    raise ValueError("bench-error cần một thông báo lỗi")
                self.bench_run.fail(obj["error"])
            else:
                self.bench_run.submit(obj)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send(400, json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"))
            return
        try:
            self._send(200, b'{"ok":true}')
        finally:
            if path == "/bench":
                self.bench_run.done.set()


def make_bench_server(tuning, seed, started, duration=None):
    """Độc lập với live.py: không sửa handler cho các game đang chơi."""
    run = BenchRun(started, duration)
    server = LiveServer(LiveGame("gather", tuning, {}, seed), port=0)
    server.httpd.RequestHandlerClass = type("BoundBenchHandler", (BenchHandler,),
                                            {"game": server.game, "bench_run": run})
    return server, run


def _open_window(url):
    """Có thể chỉ định Chrome/Edge qua CHONOI_BENCH_BROWSER để mở cửa sổ riêng.

    Nếu không chỉ định, dùng trình duyệt hệ thống. Canvas vẫn render chính xác
    1280x720 pixels dù window manager không cho đổi kích thước tab.
    """
    executable = os.environ.get("CHONOI_BENCH_BROWSER")
    if executable:
        try:
            name = os.path.basename(executable).lower()
            options = (["--new-window", "--window-size=1280,720"]
                       if any(x in name for x in ("chrome", "chromium", "msedge")) else [])
            subprocess.Popen([executable, *options, url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError as exc:
            print(f"Không mở được CHONOI_BENCH_BROWSER: {exc}", file=sys.stderr)
            return False
    return webbrowser.open(url, new=1)


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(prog="chonoi.bench", description="Đo FPS render trong browser (Ticket-04).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=float, default=30.0, help="số giây đo thực (không gồm 3 giây làm nóng)")
    parser.add_argument("--out", required=True, help="file JSON kết quả (chỉ ghi nếu đo thành công)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or not 0 < args.duration <= 300:
        parser.error("--duration phải > 0 và <= 300 giây")
    try:
        tuning = load_contract()["tuning"]
        server, run = make_bench_server(tuning, args.seed, started, args.duration)
    except (BadInput, OSError, ValueError) as exc:
        print(f"Không thể khởi tạo benchmark: {exc}", file=sys.stderr)
        return 1
    server.start()
    url = f"{server.url}?bench=1&duration={args.duration:g}"
    try:
        # Trình duyệt chạy JS/canvas thật. Không dùng vòng lặp Python để giả lập FPS.
        if not _open_window(url):
            print("Không mở được trình duyệt. Cần desktop/browser thật để đo FPS.", file=sys.stderr)
            return 1
        print(f"Đang đo cảnh Gather 1280x720 trên trình duyệt: {url}", flush=True)
        if os.path.exists(args.out):
            print(f"Lưu ý: {args.out} là kết quả CŨ; lần này thất bại sẽ không cập nhật file.", flush=True)
        timeout = args.duration + 33.0  # 3 s warmup + thời gian mở trang/trễ mạng hợp lý.
        if not run.done.wait(timeout):
            if run.first_frame is None:
                print("Benchmark timeout: chưa nhận khung hình đầu tiên; kiểm tra tab có đang ở phía trước và có tiêu điểm hay không. Không cập nhật bench.json.", file=sys.stderr)
            else:
                print("Benchmark timeout: đã bắt đầu nhưng trình duyệt không gửi kết quả; kiểm tra tab có bị dừng, mất tiêu điểm hoặc lỗi JavaScript hay không. Không cập nhật bench.json.", file=sys.stderr)
            return 1
        if run.error is not None:
            print(f"Benchmark bị gián đoạn: {run.error}; không cập nhật bench.json.", file=sys.stderr)
            return 1
        if run.data is None:
            print("Trình duyệt không tạo được dữ liệu benchmark hợp lệ.", file=sys.stderr)
            return 1
        out = os.fspath(args.out)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        # Ghi atomically để tránh bench.json nửa chừng khi lỗi.
        tmp = out + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(run.data, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.write("\n")
            os.replace(tmp, out)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        print(f"Benchmark thành công: {out} — {run.data}", flush=True)
        return 0
    except (OSError, KeyboardInterrupt) as exc:
        print(f"Benchmark không hoàn tất: {exc}", file=sys.stderr)
        return 1
    finally:
        server.stop()


if __name__ == "__main__":
    sys.exit(main())
