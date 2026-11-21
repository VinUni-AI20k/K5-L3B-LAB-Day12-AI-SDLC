"""The loopback Chromium DevTools transport used by the render benchmark."""

import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

_BINDING = "chonoiBenchFrame"


def browser_executable():
    configured = os.environ.get("CHONOI_BROWSER")
    if configured:
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        raise RuntimeError(f"Không chạy được trình duyệt từ CHONOI_BROWSER: {configured}")

    for executable in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge"):
        resolved = shutil.which(executable)
        if resolved:
            return resolved

    windows_apps = ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe")
    mac_apps = (
        "Google Chrome.app/Contents/MacOS/Google Chrome",
        "Chromium.app/Contents/MacOS/Chromium",
        "Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    )
    windows_roots = [Path(os.environ[key]) for key in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData") if key in os.environ]
    mac_roots = [Path("/Applications"), Path.home() / "Applications"]
    for roots, apps in ((windows_roots, windows_apps), (mac_roots, mac_apps)):
        for root in roots:
            for app in apps:
                candidate = root / app
                if candidate.is_file():
                    return str(candidate)
    raise RuntimeError("Cần Chrome hoặc Chromium. Đặt CHONOI_BROWSER nếu trình duyệt nằm ngoài vị trí chuẩn.")


def _target_url(profile, process):
    endpoint = profile / "DevToolsActivePort"
    opener = build_opener(ProxyHandler({}))
    deadline = time.perf_counter() + 15
    while process.poll() is None and time.perf_counter() < deadline:
        try:
            port = int(endpoint.read_text(encoding="utf-8").splitlines()[0])
            with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=1) as response:
                targets = json.load(response)
            for target in targets:
                if target.get("type") == "page":
                    return target["webSocketDebuggerUrl"]
        except (OSError, ValueError, IndexError):
            pass
        time.sleep(.05)
    raise RuntimeError("Không kết nối được với trang Chromium đã mở cho benchmark.")


class DevTools:
    """One local debugger connection. Frames are text messages or WebSocket control frames."""

    def __init__(self, url):
        address = urlsplit(url)
        if address.scheme != "ws" or address.hostname != "127.0.0.1":
            raise RuntimeError("Địa chỉ Chromium DevTools phải là loopback.")
        self.socket = socket.create_connection((address.hostname, address.port), timeout=15)
        self.reader = self.socket.makefile("rb")
        self.sequence = 0
        self.pending_frames = []
        try:
            self._upgrade(address)
        except BaseException:
            self.close()
            raise

    def _upgrade(self, address):
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (f"GET {address.path} HTTP/1.1\r\nHost: {address.netloc}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.socket.sendall(request.encode("ascii"))
        status = self.reader.readline()
        headers = {}
        while line := self.reader.readline():
            if line == b"\r\n":
                break
            name, _, value = line.partition(b":")
            headers[name.lower()] = value.strip()
        digest = hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        if not status.startswith(b"HTTP/1.1 101 ") or headers.get(b"sec-websocket-accept") != base64.b64encode(digest):
            raise RuntimeError("Chromium từ chối kết nối WebSocket.")

    def _write(self, opcode, body):
        length = len(body)
        if length < 126:
            size = bytes([0x80 | length])
        elif length < 65536:
            size = b"\xfe" + struct.pack("!H", length)
        else:
            size = b"\xff" + struct.pack("!Q", length)
        mask = os.urandom(4)
        data = bytes(value ^ mask[index % 4] for index, value in enumerate(body))
        self.socket.sendall(bytes([0x80 | opcode]) + size + mask + data)

    def _read(self, size):
        data = self.reader.read(size)
        if len(data) != size:
            raise RuntimeError("Chromium đóng kết nối giữa lúc đo.")
        return data

    def _message(self):
        fragments = []
        while True:
            first, second = self._read(2)
            kind = first & 15
            size = second & 127
            if size in (126, 127):
                size, = struct.unpack("!H" if size == 126 else "!Q", self._read(2 if size == 126 else 8))
            if second & 128 or size > 16 * 1024 * 1024:
                raise RuntimeError("Khung WebSocket của Chromium không hợp lệ.")
            payload = self._read(size)
            if kind == 8:
                raise RuntimeError("Chromium đóng trang benchmark.")
            if kind == 9:
                self._write(10, payload)
                continue
            if kind == 10:
                continue
            fragments.append(payload)
            if first & 128:
                return json.loads(b"".join(fragments))

    def send(self, method, **params):
        self.sequence += 1
        self._write(1, json.dumps({"id": self.sequence, "method": method, "params": params}).encode("utf-8"))
        return self.sequence

    @staticmethod
    def _binding(message):
        method = message.get("method")
        params = message.get("params", {})
        if method == "Runtime.exceptionThrown":
            details = params["exceptionDetails"]
            reason = details.get("exception", {}).get("description", details.get("text"))
            raise RuntimeError(f"Lỗi JavaScript trong benchmark: {reason}")
        if method == "Runtime.bindingCalled" and params.get("name") == _BINDING:
            payload = params["payload"]
            if payload.startswith("error:"):
                raise RuntimeError(payload.removeprefix("error:"))
            return payload
        return None

    def call(self, method, **params):
        command = self.send(method, **params)
        while True:
            message = self._message()
            if message.get("id") == command:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']['message']}")
                return message.get("result", {})
            payload = self._binding(message)
            if payload is not None:
                self.pending_frames.append((payload, time.perf_counter()))

    def open_page(self, url, width, height):
        self.call("Runtime.enable")
        self.call("Runtime.addBinding", name=_BINDING)
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
        result = self.call("Page.navigate", url=url)
        if result.get("errorText"):
            raise RuntimeError(result["errorText"])

    def frames(self):
        yield from self.pending_frames
        self.pending_frames.clear()
        while True:
            message = self._message()
            received = time.perf_counter()
            payload = self._binding(message)
            if payload is not None:
                yield payload, received

    def close(self):
        self.reader.close()
        self.socket.close()


@contextmanager
def chromium(executable, scratch, width, height):
    profile = scratch / "profile"
    args = [executable, "--headless", "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
            f"--window-size={width},{height}", f"--user-data-dir={profile}", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", "--disable-background-networking"]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        args.append("--no-sandbox")
    args.append("about:blank")
    connection = None
    with (scratch / "chromium.log").open("wb") as log:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=log)
        try:
            connection = DevTools(_target_url(profile, process))
            yield connection
        finally:
            if connection is not None:
                try:
                    connection.send("Browser.close")
                except OSError:
                    pass
                finally:
                    connection.close()
            try:
                process.wait(timeout=3 if connection is not None else 0)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
