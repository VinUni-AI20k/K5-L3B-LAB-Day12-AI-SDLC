"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live [--mode gather|quan|day] [--days N] [--seed N] [--port 8000]

Không có --mode thì mở MENU chính (P2-08): chọn gather, quan hoặc day (1..N Ngày) trên trình duyệt.

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và các API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`;
                    ở menu trả {"screen": "menu", "modes": [...], "days_max": N, "seed": N}
    POST /input  -> {"move": [a, b], "interact", "catch", "pause", "shop_done": bool, "buy": "oxygen"|"hp"}
    POST /start  -> {"mode": "gather"|"quan"|"day", "days": 1..N}  (từ menu vào chơi)
    POST /menu   -> về menu chính
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import alerts, freshness_view
from .contract import load_contract
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import read_inventory_for
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40
MODES = ("gather", "quan", "day")
MAX_BUY_LEN = 32


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=1,
                 contract_version="1.1"):
        """mode=None: mở menu chính, chưa dựng sim cho tới POST /start."""
        self.tuning = tuning
        self.contract_version = contract_version
        self.seed = seed
        self.days_max = len(tuning.get("day_plan", [])) or 1
        self._scenario, self._inventory = scenario, inventory
        self.inventory_out = inventory_out
        self.fixed_mode = mode is not None  # có --mode: chạy thẳng chế độ đó, không có menu
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.session = None
        self.mode, self.days = None, days
        self.inputs = LiveInputs()
        self.events = []
        self.error = None
        if mode is not None:
            self._configure(mode, days)
            self._reset()

    def _configure(self, mode, days):
        self.mode, self.days = mode, days
        self._args = (mode, self.tuning, self._scenario, self.seed,
                      self._inventory if mode == "quan" else None, days, self.contract_version)

    def _reset(self):
        self.session = Session(*self._args)
        self.inputs = LiveInputs()
        self.events = self.session.start_rows()  # day: day_start, day_plan, phase_start ở tick 0
        self._saved = False
        self.error = None

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s is None or s.done:  # đang ở menu hoặc đã xong
            return
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out and self.mode == "gather":
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def _meta(self, snap):
        """Tuning của pha đang chạy (day đổi pha gather -> quan -> shop)."""
        phase = snap.get("phase") or self.mode
        return self.tuning.get(phase, {})

    def state_json(self) -> bytes:
        with self._lock:
            if self.session is None:
                menu = {"screen": "menu", "modes": list(MODES), "days_max": self.days_max, "seed": self.seed,
                        "finished": False, "error": None}
                return json.dumps(menu, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            snap = self.session.snapshot()
            snap["screen"] = "game"
            snap["meta"] = self._meta(snap)
            snap["alerts"] = alerts.compute(snap, self.tuning)  # AC-P4-04: chỉ có ở cửa sổ live
            fresh = freshness_view.view(snap, self.tuning)  # P3-06: HUD độ tươi (None khi chưa có cá thể)
            if fresh is not None:
                snap["freshness_hud"] = fresh
            snap["fixed_mode"] = self.fixed_mode
            if self.mode == "day":
                snap["days_total"] = self.days
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "pause", "shop_done"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and not (isinstance(buy, str) and 0 < len(buy) <= MAX_BUY_LEN):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            if self.session is None:
                raise ValueError("đang ở menu: POST /start trước")
            self.inputs.set(move, buy=buy, **buttons)

    def begin(self, body):
        """Từ menu vào chơi (POST /start)."""
        mode, days = body.get("mode"), body.get("days", 1)
        if mode not in MODES:
            raise ValueError(f"mode phải thuộc {list(MODES)}")
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= self.days_max:
            raise ValueError(f"days phải là số nguyên trong [1, {self.days_max}]")
        with self._lock:
            if self.fixed_mode:
                raise ValueError("đã chạy với --mode cố định")
            self._configure(mode, days)
            self._reset()

    def to_menu(self):
        with self._lock:
            if self.fixed_mode:
                raise ValueError("đã chạy với --mode cố định")
            self.session, self.mode = None, None
            self.inputs, self.events, self.error = LiveInputs(), [], None

    def restart(self):
        with self._lock:
            if self.session is not None:
                self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path in ("/input", "/start"):
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                if path == "/input":
                    self.game.set_input(body)
                else:
                    self.game.begin(body)
            elif path == "/menu":
                self.game.to_menu()
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", choices=list(MODES), help="bỏ trống = mở menu chính")
    p.add_argument("--days", type=int, default=1, help="chỉ với day: số Ngày")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        if a.scenario and a.mode is None:
            raise BadInput("--scenario cần --mode")
        contract = load_contract()
        tuning, version = contract["tuning"], contract["contract_version"]
        days_max = len(tuning.get("day_plan", [])) or 1
        if not 1 <= a.days <= days_max:
            raise BadInput(f"--days phải trong [1, {days_max}]")
        if a.days != 1 and a.mode != "day":
            raise BadInput("--days chỉ dùng với day")
        scenario = load_scenario(a.scenario, a.mode, tuning, version) if a.mode else {}
        fresh_initial = tuning.get("freshness", {}).get("initial", 100)
        inventory = read_inventory_for(a.inventory, version, fresh_initial) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, a.days, version)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode or 'menu'}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
