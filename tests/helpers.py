"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import atexit
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


@lru_cache(maxsize=None)
def _interpreter_runs(name):
    try:
        return subprocess.run([name, "-c", "pass"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ.
    Nếu lệnh bắt đầu bằng python3 hoặc python mà máy không có (Windows thường chỉ có `python`), dùng python đang chạy test."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python3", "python") and not _interpreter_runs(cmd[0]):
        cmd[0] = sys.executable
    return cmd


@lru_cache(maxsize=None)
def legacy_env():
    """Môi trường chạy headless với bản contract 1.1 (CHONOI_CONTRACT): các test hồi quy Phase 1-2 kiểm luật kho đếm.

    Từ P3-08 `game.contract.json` là 1.2 (kho cá thể, breaking). Test Phase 1-2 qua `run_headless` vẫn chạy với bản 1.1
    sinh từ chính file contract (chỉ đổi `contract_version`); kiểm đường 1.2 nằm ở tests/test_p3_v12_cli.py
    (`run_headless(..., v12=True)`) và tools/smoke_phase3.py.
    """
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        data = json.load(f)
    data["contract_version"] = "1.1"
    d = tempfile.mkdtemp(prefix="contract-v11-")
    path = os.path.join(d, "game.contract.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    atexit.register(shutil.rmtree, d, True)
    return {**os.environ, "CHONOI_CONTRACT": path}


def run_headless(*args, cwd=ROOT, v12=False):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr). Mặc định dùng contract 1.1 (hồi quy Phase 1-2);
    `v12=True` dùng đúng game.contract.json (1.2)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=None if v12 else legacy_env())  # stderr của headless là UTF-8; Windows mặc định cp1252
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
