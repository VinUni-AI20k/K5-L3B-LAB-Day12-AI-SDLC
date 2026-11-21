"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan [--seed N] [--port 8000]

Máy chủ HTTP nhỏ phục vụ client và các API live:
    GET  /config -> tuning đọc từ game.contract.json
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)
    POST /play -> chọn day, gather, quan hoặc menu; POST /continue -> bàn giao kho sáng sang tối

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

from .contract import DEFAULT_PATH, load_contract
from .errors import BadInput
from .inputs import BUTTONS_V10, InputState, normalize
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
SAMPLE_INVENTORY = os.path.join(os.path.dirname(DEFAULT_PATH), "docs", "contracts", "inventory.sample.json")
WEB_FILES = {"index.html": "text/html", "styles.css": "text/css", "phase2.preview.json": "application/json",
             **dict.fromkeys(("app.js", "adapter.js", "scenes.js", "art.js", "preview.js",
                              "campaign.js", "phase2-preview.js"), "text/javascript")}
MAX_BODY = 4096
RECENT_EVENTS = 40


class _TickInputs:
    """Nhận trạng thái phím từ HTTP và cấp một xung cho mỗi cạnh lên ở tick live."""

    def __init__(self):
        self.move = (0.0, 0.0)
        self.down = dict.fromkeys(BUTTONS_V10, False)
        self.pending = dict.fromkeys(BUTTONS_V10, 0)
        self.pulses = set()

    def set(self, move, **buttons):
        if move is not None:
            self.move = normalize(move)
        for name, down in buttons.items():
            if down and not self.down[name]:
                self.pending[name] += 1
            self.down[name] = down

    def advance(self):
        # Kể cả hai cú bấm đến giữa cùng hai tick, mỗi xung vẫn có một tick nhả sau nó.
        self.pulses = {name for name in BUTTONS_V10 if self.pending[name] and name not in self.pulses}
        for name in self.pulses:
            self.pending[name] -= 1
        return InputState(self.move, {name: name in self.pulses for name in BUTTONS_V10}, self.pulses)


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, *, autoplay=True):
        self.tuning = tuning
        self.seed = seed
        self._launch_mode = mode
        self._launch_scenario = scenario
        self._launch_inventory = inventory
        self._browser_inventory_path = inventory_out or "inventory.json"
        self._session_id = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._begin(mode, mode, scenario, inventory, inventory_out)
        self.active = autoplay

    @property
    def mode(self):
        return self.session.mode

    def _begin(self, play_mode, mode, scenario, inventory, inventory_out):
        self.session = Session(mode, self.tuning, scenario, self.seed, inventory)
        self._phase_args = (play_mode, mode, scenario, inventory, inventory_out)
        self.play_mode = play_mode
        self.inventory_out = inventory_out
        self.active = True
        self._session_id += 1
        self.inputs = _TickInputs()
        self.events = []
        self._saved = False
        self._inventory_error = None
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
        tick_s = 1.0 / self.tuning["tick_hz"]
        while not self._stop.is_set():
            nxt += tick_s
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
        if not self.active or s.done:
            return
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if self.mode == "gather" and s.done and self.inventory_out:
            self._save_inventory()

    def _save_inventory(self):
        try:
            self.session.write_inventory_if_done(self.inventory_out)
        except OSError as e:
            self._inventory_error = str(e)
            sys.stderr.write(f"lỗi ghi kho: {e}\n")
        else:
            self._saved = True
            self._inventory_error = None

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            snap["meta"] = self.tuning[self.mode]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            snap["session_id"] = self._session_id
            snap["inventory_saved"] = self._saved
            snap["inventory_file"] = os.path.basename(self.inventory_out) if self.inventory_out else None
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in BUTTONS_V10:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        with self._lock:
            self.inputs.set(move, **buttons)

    def restart(self):
        with self._lock:
            self._begin(*self._phase_args)

    def play(self, choice):
        if choice not in ("day", "gather", "quan", "menu"):
            raise ValueError("Chế độ chơi phải là day, gather, quan hoặc menu.")
        with self._lock:
            if choice == "menu":
                self.active = False
                return
            mode = "gather" if choice == "day" else choice
            scenario = self._launch_scenario if mode == self._launch_mode else {}
            if mode == "gather":
                self._begin(choice, mode, scenario, None, self._browser_inventory_path)
            else:
                inventory = self._launch_inventory
                if inventory is None and "stock" not in scenario:
                    path = self._browser_inventory_path
                    inventory = read_inventory(path if os.path.exists(path) else SAMPLE_INVENTORY)
                self._begin(choice, mode, scenario, inventory, None)

    def continue_day(self):
        with self._lock:
            if (self.play_mode != "day" or not self.active or self.mode != "gather"
                    or not any(row["name"] == "gather_end" for row in self.events)):
                raise ValueError("Cần hoàn thành buổi sáng trong chế độ Chơi trọn ngày.")
            if not self._saved:
                self._save_inventory()
            if not self._saved:
                raise OSError(f"Chưa ghi được kho: {self._inventory_error}")
            inventory = read_inventory(self.inventory_out)
            if inventory != self.session.sim.inventory_items():
                raise BadInput("File kho đã thay đổi sau khi chốt buổi sáng.")
            self._begin("day", "quan", {}, inventory, None)


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
        elif path == "/config":
            self._send(200, json.dumps(self.game.tuning, ensure_ascii=False).encode("utf-8"))
        elif (name := "index.html" if path == "/" else path.removeprefix("/")) in WEB_FILES:
            try:
                with open(os.path.join(WEB_DIR, name), "rb") as f:
                    self._send(200, f.read(), f"{WEB_FILES[name]}; charset=utf-8")
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
            if path in ("/input", "/play"):
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                if path == "/input":
                    self.game.set_input(body)
                else:
                    self.game.play(body.get("mode"))
            elif path == "/continue":
                self.game.continue_day()
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, BadInput) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        except OSError as e:
            self._send(500, json.dumps({"error": str(e)}).encode("utf-8"))
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
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi Quán Ăn Chợ Nổi trên trình duyệt.")
    p.add_argument("--mode", required=True, choices=["gather", "quan"])
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
        tuning = load_contract()["tuning"]
        inventory = read_inventory(a.inventory) if a.inventory else None
        scenario = load_scenario(a.scenario, a.mode, tuning, inventory=inventory)
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, autoplay=False)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Open {server.url} ({a.mode}, seed {a.seed}). Ctrl+C to stop.", flush=True)
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
