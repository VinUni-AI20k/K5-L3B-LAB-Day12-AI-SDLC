"""Kiểm tính tất định: chạy headless hai lần cùng seed, so output từng byte.

    python3 tools/check_determinism.py [--mode gather|quan|day|all] [--seed 1] [--ticks 600] [--inputs file.json]

Mặc định chạy cả hai chế độ với một bộ input bơi/đi có nút `interact` và `catch`, để đường chạy có chuyển
động thật (không chỉ đứng yên). Thoát 0 nếu mọi cặp giống hệt, 1 nếu có cặp khác (in dòng đầu tiên lệch).
Chế độ `day` chạy `--days 2` đến hết (days_complete) để qua đủ ba pha và hai Ngày, bỏ qua `--ticks`.
Lệnh headless lấy từ `headless_cmd` trong game.contract.json; nếu `python3` không có trên máy
(Windows) thì dùng python đang chạy script này. Chỉ dùng thư viện chuẩn.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Bơi chéo xuống rồi đi ngang, bấm catch/interact vài lần.
DEFAULT_FRAMES = {"frames": [
    {"tick": 0, "move": [1, 0.5]},
    {"tick": 60, "move": [1, 0], "catch": True},
    {"tick": 61, "catch": False},
    {"tick": 120, "move": [-0.5, -1], "interact": True},
    {"tick": 121, "interact": False},
    {"tick": 240, "move": [0, 1], "catch": True},
    {"tick": 241, "catch": False},
    {"tick": 300, "move": [1, -1], "interact": True},
    {"tick": 301, "interact": False},
]}


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python3", "python") and shutil.which(cmd[0]) is None:
        cmd[0] = sys.executable
    return cmd


DAY_DAYS = 2
DAY_TICKS = 200000  # dư để chạy hết DAY_DAYS Ngày; dừng sớm khi days_complete


def run_once(mode, seed, ticks, inputs, out):
    if mode == "day":
        ticks = DAY_TICKS
    args = [*headless_cmd(), "--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", out,
            "--inputs", inputs]
    if mode == "day":
        args += ["--days", str(DAY_DAYS)]
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


def first_diff(a, b):
    """Số dòng (từ 1) đầu tiên khác nhau của hai file, hoặc None nếu giống hệt."""
    with open(a, "rb") as fa, open(b, "rb") as fb:
        da, db = fa.read(), fb.read()
    if da == db:
        return None
    la, lb = da.split(b"\n"), db.split(b"\n")
    for i, (x, y) in enumerate(zip(la, lb), 1):
        if x != y:
            return i
    return min(len(la), len(lb)) + 1


def check_mode(mode, seed, ticks, inputs, tmp):
    outs = [os.path.join(tmp, f"{mode}-{k}.jsonl") for k in (1, 2)]
    for out in outs:
        code, err = run_once(mode, seed, ticks, inputs, out)
        if code != 0:
            return f"{mode}: headless thoát mã {code}: {err}"
    line = first_diff(*outs)
    if line is not None:
        return f"{mode}: hai lần chạy cùng seed {seed} khác nhau từ dòng {line} ({outs[0]} vs {outs[1]})"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=["gather", "quan", "day", "all"], default="all")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--inputs", help="file inputs JSON (mặc định: bộ input có chuyển động và nút bấm)")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Windows (cp1252) không in được tiếng Việt nếu không đổi
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    modes = ["gather", "quan", "day"] if a.mode == "all" else [a.mode]
    with tempfile.TemporaryDirectory() as tmp:
        inputs = a.inputs
        if inputs is None:
            inputs = os.path.join(tmp, "inputs.json")
            with open(inputs, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_FRAMES, f)
        problems = [p for p in (check_mode(m, a.seed, a.ticks, inputs, tmp) for m in modes) if p]
    if problems:
        print("KHÔNG TẤT ĐỊNH:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {', '.join(modes)} giống từng byte qua 2 lần chạy (seed {a.seed}, {a.ticks} tick)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
