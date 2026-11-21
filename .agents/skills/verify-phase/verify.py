"""Kiểm chứng một phase và lưu bằng chứng vào docs/proof/phase-<n>/.

    python .agents/skills/verify-phase/verify.py --phase 1

Làm 4 việc (chỉ thư viện chuẩn, chạy được trên Windows/Linux/macOS):
  1. chạy toàn bộ unittest           -> tests.txt
  2. headless gather + quan, mỗi mode 2 lần cùng seed, so từng byte -> determinism.txt
  3. gather cập bến ghi kho -> quan đọc kho, so stock -> inventory.txt
  4. tools/check_team.py              -> team.txt
Tổng hợp ở summary.md. Mã thoát 0 nếu mọi bước đạt, 1 nếu có bước không đạt.
Headless chạy đúng `headless_cmd` trong game.contract.json (giống bộ chấm).
"""

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def run(cmd, env=None):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def step_tests():
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(["tests", "."]))
    code, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], env)
    return code == 0, out


def step_determinism(tmp):
    lines, ok = [], True
    for mode in ("gather", "quan"):
        outs = []
        for i in (1, 2):
            path = os.path.join(tmp, f"{mode}{i}.jsonl")
            code, err = run([*headless_cmd(), "--mode", mode, "--seed", "1", "--ticks", "600", "--out", path])
            if code != 0:
                ok = False
                lines.append(f"{mode} lần {i}: mã thoát {code}\n{err}")
                break
            with open(path, "rb") as f:
                outs.append(f.read())
        if len(outs) == 2:
            same = outs[0] == outs[1]
            ok &= same
            lines.append(f"{mode}: seed 1, 600 tick, {len(outs[0])} byte -> {'GIỐNG từng byte' if same else 'KHÁC'}")
    return ok, "\n".join(lines)


def step_inventory(tmp):
    sc = os.path.join(tmp, "sc.json")
    inp = os.path.join(tmp, "in.json")
    inv = os.path.join(tmp, "kho.json")
    with open(sc, "w", encoding="utf-8") as f:
        json.dump({"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}}, f)
    with open(inp, "w", encoding="utf-8") as f:
        json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
    code, err = run([*headless_cmd(), "--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                     "--inputs", inp, "--inventory-out", inv, "--out", os.path.join(tmp, "g.jsonl")])
    if code != 0 or not os.path.exists(inv):
        return False, f"gather không ghi được kho (mã {code})\n{err}"
    q = os.path.join(tmp, "q.jsonl")
    code, err = run([*headless_cmd(), "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", q])
    if code != 0:
        return False, f"quan không đọc được kho (mã {code})\n{err}"
    with open(inv, encoding="utf-8") as f:
        saved = json.load(f)
    with open(q, encoding="utf-8") as f:
        stock = json.loads(f.readline())["stock"]
    same = saved["items"] == stock
    return same, f"kho ghi: {json.dumps(saved, ensure_ascii=False)}\nquan stock: {json.dumps(stock, ensure_ascii=False)}\n-> {'KHỚP' if same else 'LỆCH'}"


def step_team():
    code, out = run([sys.executable, "tools/check_team.py"])
    return code == 0, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, type=int)
    args = ap.parse_args()
    proof = os.path.join(ROOT, "docs", "proof", f"phase-{args.phase}")
    os.makedirs(proof, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, fname, fn in (("Unit + smoke test", "tests.txt", step_tests),
                                ("Tất định (2 lần cùng seed)", "determinism.txt", lambda: step_determinism(tmp)),
                                ("Kho gather -> quan", "inventory.txt", lambda: step_inventory(tmp)),
                                ("Danh sách thành viên", "team.txt", step_team)):
            ok, out = fn()
            with open(os.path.join(proof, fname), "w", encoding="utf-8", newline="\n") as f:
                f.write(out.rstrip() + "\n")
            rows.append((name, fname, ok))
            print(f"[{'ĐẠT' if ok else 'CHƯA ĐẠT'}] {name} -> docs/proof/phase-{args.phase}/{fname}")
    commit = run(["git", "rev-parse", "--short", "HEAD"])[1].strip()
    with open(os.path.join(proof, "summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Bằng chứng Phase {args.phase}\n\n")
        f.write(f"- Commit: `{commit}`  ·  Lúc chạy: {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(f"- Lệnh: `python .agents/skills/verify-phase/verify.py --phase {args.phase}`\n\n")
        f.write("| Kiểm tra | File | Kết quả |\n|---|---|---|\n")
        for name, fname, ok in rows:
            f.write(f"| {name} | [{fname}]({fname}) | {'đạt' if ok else 'chưa đạt'} |\n")
    return 0 if all(ok for _, _, ok in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
