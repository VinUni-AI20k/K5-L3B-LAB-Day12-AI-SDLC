"""Kiểm tất định: cùng seed + tham số + đầu vào -> JSONL và file kho giống từng byte. Chỉ dùng thư viện chuẩn.

Chạy từ gốc repo: python3 .agents/skills/kiem-tat-dinh/kiem_tat_dinh.py [--seeds 1 42 -7] [--ticks 3600] [--proof <thư mục>]
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SAMPLE_INV = os.path.join(ROOT, "docs", "contracts", "inventory.sample.json")

# Lặn xuống chỗ đàn F1 [15,5], bắt, nổi lên, bơi tới nút N1 [12,0], hái, về bến.
GATHER_INPUTS = {"frames": [
    {"tick": 0, "move": [1, 0.4]},
    {"tick": 200, "move": [0, 0], "catch": True},
    {"tick": 201, "catch": False, "move": [0, -1]},
    {"tick": 330, "move": [-1, 0]},
    {"tick": 380, "move": [0, 0], "interact": True},
    {"tick": 381, "interact": False, "move": [-1, 0]},
    {"tick": 900, "move": [0, 0], "interact": True},
    {"tick": 901, "interact": False},
]}


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python3", "python"):
        cmd[0] = sys.executable  # Windows thường không có `python3`
    return cmd


def run(args):
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


def read_bytes(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def first_diff(a, b):
    la, lb = (a or b"").splitlines(), (b or b"").splitlines()
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"dòng {i + 1}:\n    lần 1: {x[:200]!r}\n    lần 2: {y[:200]!r}"
    return f"số dòng khác: {len(la)} vs {len(lb)}"


def scenarios(w, seed, ticks):
    inputs = os.path.join(w, "inputs.json")
    with open(inputs, "w", encoding="utf-8") as f:
        json.dump(GATHER_INPUTS, f)
    base = ["--seed", str(seed), "--ticks", str(ticks)]
    return {
        "gather-tu-do": ["--mode", "gather", *base],
        "gather-inputs": ["--mode", "gather", *base, "--inputs", inputs, "--inventory-out", "{kho}"],
        "quan-kho-mau": ["--mode", "quan", *base, "--inventory", SAMPLE_INV],
        "quan-khong-kho": ["--mode", "quan", *base],
    }


def run_twice(w, name, args):
    outs = []
    for k in (1, 2):
        out, kho = os.path.join(w, f"{name}-{k}.jsonl"), os.path.join(w, f"{name}-{k}-kho.json")
        code, err = run([a.replace("{kho}", kho) for a in args] + ["--out", out])
        if code != 0:
            return False, f"mã thoát {code}: {err}", None
        outs.append((read_bytes(out), read_bytes(kho)))
    (j1, k1), (j2, k2) = outs
    if j1 != j2:
        return False, "JSONL khác — " + first_diff(j1, j2), j1
    if k1 != k2:
        return False, f"file kho khác: {k1!r} vs {k2!r}", j1
    return True, f"{len(j1)} byte" + (f", kho {k1.decode().strip()}" if k1 else ""), j1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 42, -7])
    ap.add_argument("--ticks", type=int, default=3600)
    ap.add_argument("--proof", help="thư mục lưu bằng chứng (tat-dinh.txt)")
    opt = ap.parse_args()

    lines, fails = [], 0
    w = tempfile.mkdtemp(prefix="tat-dinh-")
    try:
        quan_by_seed = {}
        for seed in opt.seeds:
            for name, args in scenarios(w, seed, opt.ticks).items():
                ok, detail, jsonl = run_twice(w, f"s{seed}-{name}", args)
                fails += not ok
                lines.append(f"{'ĐẠT ' if ok else 'TRƯỢT'} | seed {seed:>4} | {name:<15} | {detail}")
                if name == "quan-kho-mau":
                    quan_by_seed[seed] = jsonl
        distinct = {v for v in quan_by_seed.values() if v is not None}
        if len(quan_by_seed) > 1 and len(distinct) == 1:
            lines.append("CẢNH BÁO | quan-kho-mau giống nhau ở mọi seed (bình thường khi chưa có lát 3)")
        total = len(opt.seeds) * 4
        lines.append(f"\n{total - fails}/{total} cặp giống từng byte · seeds {opt.seeds} · {opt.ticks} tick")
        report = "\n".join(lines)
        print(report)
        if opt.proof:
            out = os.path.join(ROOT, opt.proof)
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "tat-dinh.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write(report + "\n")
            print(f"Đã lưu bằng chứng vào {opt.proof}")
        return 1 if fails else 0
    finally:
        shutil.rmtree(w, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
