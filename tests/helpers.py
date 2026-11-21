"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import sys
import tempfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def item_schema_enabled():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as file:
        version = json.load(file)["contract_version"]
    return tuple(map(int, version.split("."))) >= (1, 2)


def ingredient_fixture(kinds):
    """Giỏ fixture theo schema của bản chạy, giữ thứ tự nhặt."""
    return [{"id": f"I{i}", "kind": kind, "fresh": 100}
            for i, kind in enumerate(kinds, 1)] if item_schema_enabled() else list(kinds)


def stock_counts(items):
    return dict(Counter(item["kind"] for item in items)) if isinstance(items, list) else items


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        command = shlex.split(json.load(f)["headless_cmd"])
    if sys.platform == "win32" and command[:3] == ["python3", "-m", "chonoi.headless"]:
        command[0] = sys.executable
    return command


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, env=environment, capture_output=True, encoding="utf-8")
    return p.returncode, p.stderr


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def snapshots(rows):
    return [r for r in rows if r["type"] == "snapshot"]


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def close(a, b, tol=0.1):
    return abs(a - b) <= tol


def dist(p, q):
    return math.dist(p, q)


class Workdir:
    """Thư mục tạm tự dọn: with Workdir() as w: w.path('x.json')."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *a):
        self._d.cleanup()

    def path(self, name):
        return os.path.join(self._d.name, name)
