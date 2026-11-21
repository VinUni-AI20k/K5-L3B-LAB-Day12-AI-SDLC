"""Cổng kiểm Phase 1 bằng một lệnh: python3 tools/run_checks.py

Chạy 3 việc, in bảng PASS/FAIL, ghi bằng chứng vào docs/proof/phase-1/checks-latest.md:
  1. unit + hộp đen: python3 -m unittest discover -s tests
  2. smoke hai tiến trình: gather cập bến -> file kho -> quan đọc kho
  3. tất định: cùng seed, cùng inputs -> JSONL giống từng byte
"""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF = os.path.join(ROOT, "docs", "proof", "phase-1")


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd = shlex.split(json.load(f)["headless_cmd"])
    if cmd and cmd[0] in ("python3", "python"):
        cmd[0] = sys.executable  # dùng đúng interpreter đang chạy
    return cmd


def run(args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def check_unittest(tmp):
    env = dict(os.environ, PYTHONPATH=f"tests:{ROOT}")
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                       cwd=ROOT, capture_output=True, text=True, env=env)
    tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
    return p.returncode == 0, " | ".join(tail)


def check_smoke(tmp):
    sc = write_json(os.path.join(tmp, "dock.json"),
                    {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
    inp = write_json(os.path.join(tmp, "dock-inputs.json"),
                     {"frames": [{"tick": 0, "interact": True}]})
    inv = os.path.join(tmp, "catch.json")
    g_out = os.path.join(tmp, "gather.jsonl")
    q_out = os.path.join(tmp, "quan.jsonl")
    cmd = headless_cmd()
    code, out = run([*cmd, "--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp,
                     "--ticks", "1", "--out", g_out, "--inventory-out", inv])
    if code != 0:
        return False, f"gather exit {code}: {out.strip()[-200:]}"
    if not os.path.exists(inv):
        return False, "không có file kho"
    with open(inv, encoding="utf-8") as f:
        saved = json.load(f)
    code, out = run([*cmd, "--mode", "quan", "--seed", "42", "--inventory", inv,
                     "--ticks", "0", "--out", q_out])
    if code != 0:
        return False, f"quan exit {code}: {out.strip()[-200:]}"
    with open(q_out, encoding="utf-8") as f:
        snap = json.loads(f.readline())
    want = {"bong_sung": 2, "ca_loc": 1}
    return snap.get("stock") == want, f"kho ghi {saved.get('items')} -> quán đọc {snap.get('stock')}"


def check_determinism(tmp):
    inp = write_json(os.path.join(tmp, "det.json"),
                     {"frames": [{"tick": 0, "move": [1, 1]}, {"tick": 100, "move": [0, 0]}]})
    outs = []
    for i in (1, 2):
        out = os.path.join(tmp, f"det{i}.jsonl")
        code, msg = run([*headless_cmd(), "--mode", "gather", "--seed", "7", "--ticks", "300",
                         "--inputs", inp, "--out", out])
        if code != 0:
            return False, f"lần {i} exit {code}: {msg.strip()[-200:]}"
        outs.append(out)
    a = open(outs[0], "rb").read()
    b = open(outs[1], "rb").read()
    return a == b, f"{len(a)} byte, giống nhau: {a == b}"


def main():
    os.makedirs(PROOF, exist_ok=True)
    checks = [("unittest (unit + hộp đen)", check_unittest),
              ("smoke gather -> kho -> quan", check_smoke),
              ("tất định cùng seed", check_determinism)]
    rows, ok_all = [], True
    with tempfile.TemporaryDirectory() as tmp:
        for name, fn in checks:
            ok, detail = fn(tmp)
            ok_all &= ok
            rows.append((name, "PASS" if ok else "FAIL", detail))
    print("\nCỔNG KIỂM PHASE 1\n" + "=" * 60)
    for name, status, detail in rows:
        print(f"[{status}] {name}\n        {detail}")
    print("=" * 60)
    print("KẾT LUẬN:", "PASS" if ok_all else "FAIL (còn luật chưa xong — xem docs/tickets/)")

    lines = [f"# Cổng kiểm Phase 1 — {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
             "| Cổng | Kết quả | Chi tiết |", "|---|---|---|"]
    lines += [f"| {n} | {s} | {d} |" for n, s, d in rows]
    lines += ["", f"**Kết luận:** {'PASS' if ok_all else 'FAIL'}", ""]
    with open(os.path.join(PROOF, "checks-latest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
