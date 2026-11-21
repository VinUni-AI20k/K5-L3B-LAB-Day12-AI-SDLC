"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan|day [--days 5] [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html`, tài nguyên tĩnh `/assets/*` và các API:
    GET  /state   -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input   -> {"move": [a, b], "interact": bool, "catch": bool, "pause": bool, "shop_done": bool, "buy": str}
    POST /restart -> chơi lại từ đầu (cùng mode, seed, scenario)
    POST /start   -> chuyển chế độ chơi từ Menu chính (`gather` | `quan` | `day`, `days`, `seed`)

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

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState, normalize
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
ASSETS_DIR = os.path.join(WEB_DIR, "assets")
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".json": "application/json; charset=utf-8",
}
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40

LIVE_BUTTONS = ("interact", "catch", "pause", "shop_done")

DEFAULT_LIVE_SHOP = {
    "max_ticks": 600,
    "upgrades": {
        "oxygen": [
            {"level": 1, "price": 200, "oxygen_max_s": 45},
            {"level": 2, "price": 400, "oxygen_max_s": 60},
        ],
        "hp": [
            {"level": 1, "price": 250, "hp_max": 4},
            {"level": 2, "price": 500, "hp_max": 5},
        ],
    },
}


def _enrich_live_tuning(tuning: dict) -> dict:
    """Bổ sung cấu hình mặc định `shop` và `day_plan` cho `chonoi.live --mode day` nếu manifest đang ở v1.0."""
    out = dict(tuning)
    if "shop" not in out:
        out["shop"] = DEFAULT_LIVE_SHOP
    if "day_plan" not in out:
        menu = out.get("menu", {})
        dish_ids = sorted(menu.keys())
        if dish_ids:
            out["day_plan"] = [
                {"day": d, "dishes": {did: 2 for did in dish_ids}}
                for d in range(1, 6)
            ]
    return out


class _LiveInputState(InputState):
    def __init__(self, move, held, edges, buy=None):
        super().__init__(move, held, edges)
        self.buy = buy


class _LiveInputs:
    """Input trực tiếp cho `chonoi.live`: hỗ trợ các nút v1.0 + v1.1 (`pause`, `shop_done`, `buy`)."""

    def __init__(self, buttons=LIVE_BUTTONS):
        self._buttons = buttons
        self._move = (0.0, 0.0)
        self._held = {b: False for b in buttons}
        self._pending = set()
        self._buy_queue = []

    def set(self, move=None, buy=None, **buttons):
        if move is not None:
            self._move = normalize(move)
        for b, v in buttons.items():
            if b not in self._held:
                continue
            if v and not self._held[b]:
                self._pending.add(b)
            self._held[b] = bool(v)
        if buy:
            self._buy_queue.append(buy)

    def advance(self) -> _LiveInputState:
        edges, self._pending = self._pending, set()
        buy = self._buy_queue.pop(0) if self._buy_queue else None
        return _LiveInputState(self._move, dict(self._held), edges, buy=buy)


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=1):
        self._base_tuning = tuning
        self.tuning = _enrich_live_tuning(tuning) if mode == "day" else tuning
        self._args = (mode, self.tuning, scenario, seed, inventory, days)
        self.mode = mode
        self.days = days
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        mode, tuning, scenario, seed, inventory, days = self._args
        self.session = Session(mode, tuning, scenario, seed, inventory, days=days)
        self.inputs = _LiveInputs()
        self.events = list(self.session.initial_event_rows())
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
        if s.done:
            return
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            phase_key = snap.get("phase") or self.mode
            base_meta = self.tuning.get(phase_key) or self.tuning.get(self.mode) or {}
            meta = dict(base_meta)
            if "menu" in self.tuning:
                meta["menu"] = self.tuning["menu"]
            if "shop" in self.tuning:
                meta["shop"] = self.tuning["shop"]
            snap["meta"] = meta
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            if self.mode == "day":
                snap["days_total"] = self.days
                snap["days_completed"] = getattr(self.session.sim, "days_completed", 0)
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in self.inputs._buttons:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and (not isinstance(buy, str) or not buy.strip()):
            raise ValueError("buy phải là chuỗi tên nâng cấp")
        with self._lock:
            self.inputs.set(move, buy=buy, **buttons)

    def restart(self):
        with self._lock:
            self._reset()

    def switch_mode(self, mode: str, days: int = 5, seed: int = None, sample_stock: bool = False):
        if mode not in ("gather", "quan", "day"):
            raise ValueError("mode phải là gather, quan hoặc day")
        if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= 5):
            raise ValueError("days phải là số nguyên trong [1, 5]")
        with self._lock:
            old_seed = self._args[3]
            new_seed = old_seed if seed is None else int(seed)
            tuning = _enrich_live_tuning(self._base_tuning) if mode == "day" else self._base_tuning
            inv = {"ca_loc": 3, "ca_linh": 6, "bong_dien_dien": 3, "bong_sung": 4} if (mode == "quan" and sample_stock) else None
            self.mode = mode
            self.days = days if mode == "day" else 1
            self.tuning = tuning
            self._args = (mode, tuning, {}, new_seed, inv, self.days)
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
        elif path.startswith("/assets/"):
            rel = path[len("/assets/"):]
            full = os.path.abspath(os.path.join(ASSETS_DIR, rel))
            base = os.path.abspath(ASSETS_DIR)
            if not (full.startswith(base + os.sep) and os.path.isfile(full)):
                self._send(404, b'{"error":"khong co asset"}')
                return
            ext = os.path.splitext(full)[1].lower()
            ctype = MIME_TYPES.get(ext, "application/octet-stream")
            try:
                with open(full, "rb") as f:
                    self._send(200, f.read(), ctype)
            except OSError:
                self._send(404, b'{"error":"khong doc duoc asset"}')
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
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path == "/start":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.switch_mode(
                    mode=body.get("mode", "day"),
                    days=body.get("days", 5),
                    seed=body.get("seed"),
                    sample_stock=bool(body.get("sample_stock", False)),
                )
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
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter + Phase 2 day/shop/pause).")
    p.add_argument("--mode", default="day", choices=["gather", "quan", "day"])
    p.add_argument("--days", type=int, default=5, help="số ngày khi chạy --mode day (1..5)")
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
        if not (1 <= a.days <= 5):
            raise BadInput("--days phải nằm trong [1, 5]")
        tuning = load_contract()["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning) if a.scenario else {}
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, days=a.days)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
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
