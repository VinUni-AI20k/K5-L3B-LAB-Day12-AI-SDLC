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


# ---- Kho cá thể v1.2 ({id, kind, fresh}) cho fixture viết từ v1.0/v1.1 ----
def items(*kinds, fresh=100, start=1):
    """items("ca_loc", "bong_sung") -> [{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def stock_of(counts, fresh=100, start=1):
    """Đổi kho đếm v1.1 {kind: n} sang mảng cá thể v1.2 (kind theo thứ tự chữ cái)."""
    return items(*[k for k in sorted(counts) for _ in range(counts[k])], fresh=fresh, start=start)


def kinds(entries):
    """Danh sách kind (giữ thứ tự) từ hold / stock / lost / items v1.2."""
    return [e["kind"] if isinstance(e, dict) else e for e in entries]


def kind_counts(entries):
    """Đếm theo kind (bỏ 0, khóa sắp xếp) để so với kỳ vọng dạng đếm cũ."""
    out = {}
    for k in kinds(entries):
        out[k] = out.get(k, 0) + 1
    return {k: out[k] for k in sorted(out)}


def locked_price(list_price, fresh_values, steps_decayed=1):
    """Giá chốt v1.2 = floor(giá niêm yết × avg_fresh / 100), sau khi kho quán đã hao `steps_decayed` bước.

    Quán hao độ tươi ĐẦU bước (docs/plan/phase-3.md, docs/clarify.md #6), nên nấu ở bước 0 đã hao 1 bước.
    Tính bằng Fraction để không lệch ở mép floor.
    """
    from fractions import Fraction
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        t = json.load(f)["tuning"]
    step = Fraction(str(t["freshness"]["quan_decay_per_s"])) / t["tick_hz"]
    vals = [max(Fraction(0), Fraction(str(v)) - step * steps_decayed) for v in fresh_values]
    return math.floor(Fraction(list_price) * (sum(vals) / len(vals)) / 100)
