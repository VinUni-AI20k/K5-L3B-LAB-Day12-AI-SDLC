"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True)
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


def tuning_v11():
    """Tuning bỏ khối freshness -> sim chạy nhánh v1.1 (kho đếm, giữ theo lượng).

    Dùng cho test in-process của luật v1.0/v1.1 mà TICKET-03 đã [THAY THẾ] (kho đếm, giữ theo lượng, giá niêm
    yết); luật v1.2 tương ứng kiểm ở test_quan_v12_stock.py, test_gather_v12.py, test_day_v12.py.
    """
    from chonoi.contract import load_contract
    t = load_contract()["tuning"]
    t.pop("freshness", None)
    return t


def hold_items(*kinds, start=1, fresh=100):
    """v1.2 (CHANGELOG "Cập nhật fixture"): ["ca_loc", ...] -> [{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def kinds_of(items):
    """Mảng cá thể -> mảng kind theo đúng thứ tự (để so với kỳ vọng v1.1)."""
    return [it["kind"] for it in items]


def counts_of(items):
    """Mảng cá thể -> dict đếm theo kind, sắp theo kind (để so với kỳ vọng kho đếm v1.1)."""
    c = {}
    for it in items:
        c[it["kind"]] = c.get(it["kind"], 0) + 1
    return {k: c[k] for k in sorted(c)}
