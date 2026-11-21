"""Kiểm bàn giao kho gather -> quan (PRD-0 mục G). Chỉ thư viện chuẩn, chạy hộp đen qua headless_cmd.

Dùng: python3 tools/check_handoff.py <gather.jsonl> <kho.json>
  1. kho.json đúng schema {"items": {kind: int > 0}}
  2. kho.json == data.inventory của gather_end (đúng một gather_end) trong gather.jsonl
  3. quan --inventory kho.json --ticks 0: snapshot tick 0 có stock == items
In bảng số lượng; mã 0 khi khớp hết, 1 khi lệch.
"""

import json
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        c = json.load(f)
    t = c["tuning"]
    # loại nguyên liệu lấy từ dữ liệu: cá (fish_yield), nút hái, công thức món
    kinds = set(t["gather"]["fish_yield"]) | {n["kind"] for n in t["gather"]["nodes"]}
    kinds |= {k for d in t["menu"].values() for k in d["recipe"]}
    return shlex.split(c["headless_cmd"]), tuple(sorted(kinds))


def main(gather_jsonl, inv_path):
    errs = []
    cmd, kinds = load_contract()
    with open(inv_path, encoding="utf-8") as f:
        inv = json.load(f)
    items = inv.get("items") if isinstance(inv, dict) and set(inv) == {"items"} else None
    if not isinstance(items, dict) or any(k not in kinds or type(v) is not int or v <= 0 for k, v in items.items()):
        errs.append(f"schema kho sai: {inv}")
        items = {}

    with open(gather_jsonl, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    ends = [r for r in rows if r["type"] == "event" and r["name"] == "gather_end"]
    end_inv = ends[0]["data"]["inventory"]["items"] if len(ends) == 1 else None
    if end_inv is None:
        errs.append(f"cần đúng 1 gather_end, thấy {len(ends)}")
    reason = ends[0]["data"]["reason"] if ends else "-"

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "quan.jsonl")
        p = subprocess.run([*cmd, "--mode", "quan", "--seed", "1", "--ticks", "0",
                            "--inventory", os.path.abspath(inv_path), "--out", out],
                           cwd=ROOT, capture_output=True, text=True)
        stock = None
        if p.returncode != 0:
            errs.append(f"quan đọc kho lỗi (mã {p.returncode}): {p.stderr.strip()}")
        else:
            with open(out, encoding="utf-8") as f:
                stock = json.loads(f.readline())["stock"]

    print(f"gather_end reason: {reason}")
    print(f"{'kind':<16}{'kho.json':>10}{'gather_end':>12}{'quan.stock':>12}")
    for k in kinds:
        a = items.get(k, 0)
        b = "?" if end_inv is None else end_inv.get(k, 0)
        c = "?" if stock is None else stock.get(k, 0)
        mark = "" if a == b == c else "  <-- LỆCH"
        print(f"{k:<16}{a:>10}{b:>12}{c:>12}{mark}")
        if mark:
            errs.append(f"lệch {k}: kho={a} gather_end={b} quan={c}")
    print(f"tổng: {sum(items.values())} món")
    for e in errs:
        print("LỖI:", e, file=sys.stderr)
    print("KẾT QUẢ:", "KHỚP" if not errs else "LỆCH")
    return 0 if not errs else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
