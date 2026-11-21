"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def to_items(x, start=1, fresh=100):
    """Fixture cũ -> kho cá thể v1.2: list kind (thứ tự vào giỏ) hoặc dict đếm (theo tên loại) -> [{id,kind,fresh}]."""
    if isinstance(x, dict):
        x = [k for k in sorted(x) for _ in range(x[k])]
    if x and isinstance(x[0], dict):
        return x
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(x)]


def kinds(items):
    """Mảng cá thể -> mảng kind (giữ thứ tự)."""
    return [it["kind"] for it in items]


def counts(items):
    """Mảng cá thể -> dict đếm theo loại (sắp theo tên)."""
    out = {}
    for it in items:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def same_items(a, b, tol=0.01):
    """Hai mảng cá thể trùng id/kind theo thứ tự, fresh lệch ≤ tol (JSONL làm tròn 3 chữ số, file giữ đủ)."""
    return len(a) == len(b) and all(x["id"] == y["id"] and x["kind"] == y["kind"] and abs(x["fresh"] - y["fresh"]) <= tol
                                    for x, y in zip(a, b))


def migrate_scenario(obj):
    """Chuyển fixture scenario viết theo v1.0/v1.1 sang v1.2 (hold/stock cá thể, reserved là mảng id).
    Chỉ đổi dạng dữ liệu, không đổi ý nghĩa: reserved theo lượng được bỏ để hệ thống tự cấp (tươi nhất, id nhỏ)."""
    if not isinstance(obj, dict):
        return obj
    g = obj.get("gather")
    if isinstance(g, dict) and isinstance(g.get("hold"), list):
        g["hold"] = to_items(g["hold"])
    q = obj.get("quan")
    if isinstance(q, dict):
        if isinstance(q.get("stock"), dict):
            q["stock"] = to_items(q["stock"])
        for c in q.get("customers", []) if isinstance(q.get("customers"), list) else []:
            if isinstance(c, dict) and isinstance(c.get("reserved"), dict):
                if c["reserved"]:
                    del c["reserved"]
                else:
                    c["reserved"] = []
    return obj


def write_json(path, obj):
    obj = migrate_scenario(obj)
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
