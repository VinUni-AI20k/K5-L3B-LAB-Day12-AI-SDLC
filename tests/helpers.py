"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def items(*kinds, fresh=100, start=1):
    """Mảng cá thể v1.2 [{id: I<n>, kind, fresh}] theo thứ tự cho trước (TICKET-03)."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def kinds_of(arr):
    """Danh sách kind của mảng cá thể (giữ thứ tự) — so với kỳ vọng P1–P2 viết theo loại."""
    return [it["kind"] for it in arr]


def counts(inv):
    """Kho v1.2 {"items":[...]} hoặc mảng cá thể -> đếm theo loại, sắp theo kind (để so kỳ vọng kho đếm P1–P2)."""
    arr = inv["items"] if isinstance(inv, dict) else inv
    out = {}
    for it in arr:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def _migrate(obj):
    """Lớp chuyển đổi fixture P1–P2 (kho đếm) -> Contract v1.2 (kho cá thể), ADR-0001 "test migration".

    Chỉ đổi khi fixture còn dạng cũ; fixture đã viết theo v1.2 giữ nguyên. Cá thể tạo ra có fresh 100, id I1, I2…
    - gather.hold ["ca_loc", ...]            -> mảng cá thể theo thứ tự
    - quan.stock {kind: n}                   -> mảng cá thể (sắp kind)
    - customers[].reserved {kind: n}         -> mảng id lấy từ stock đã đổi (chưa dùng cho đơn khác)
    - file kho {"items": {kind: n}}          -> {"items": [...]}
    """
    if not isinstance(obj, dict):
        return obj
    if set(obj) == {"items"} and isinstance(obj["items"], dict) and all(
            isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in obj["items"].values()):
        return {"items": items(*[k for k in sorted(obj["items"]) for _ in range(obj["items"][k])])}
    n = [0]

    def mk(kind_list):
        out = items(*kind_list, start=n[0] + 1)
        n[0] += len(kind_list)
        return out

    for block in [obj.get("gather"), obj] if "gather" in obj else []:
        if isinstance(block, dict) and isinstance(block.get("hold"), list) and block["hold"] \
                and isinstance(block["hold"][0], str):
            block["hold"] = mk(block["hold"])
    q = obj.get("quan")
    if isinstance(q, dict):
        stock = q.get("stock")
        if isinstance(stock, dict):
            q["stock"] = mk([k for k in sorted(stock) for _ in range(stock[k])])
        pool = list(q.get("stock") or [])
        used = set()
        for c in q.get("customers", []):
            r = c.get("reserved")
            if isinstance(r, dict):
                ids = []
                for kind in sorted(r):
                    got = [it["id"] for it in pool if it["kind"] == kind and it["id"] not in used][:r[kind]]
                    ids += got
                    used.update(got)
                c["reserved"] = ids
    return obj


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_migrate(obj), f)
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
