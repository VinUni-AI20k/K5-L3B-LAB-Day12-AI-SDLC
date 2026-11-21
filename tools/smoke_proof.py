"""Smoke hai tiến trình gather -> quan (PRD-0 mục G) và lưu bằng chứng thật vào docs/proof/<phase>/.

    python3 tools/smoke_proof.py --phase phase-1
    python3 tools/smoke_proof.py --phase phase-1 --cmd "python -m chonoi.headless"   # máy không có python3

Chạy đúng 2 lệnh của PRD bằng `headless_cmd` trong game.contract.json (hoặc --cmd), rồi kiểm:
  - cả hai mã thoát 0; gather_end reason = docked; file kho = gather_end.inventory (Contract v1.2: mảng cá thể)
  - file kho đúng id/kind của giỏ, fresh đã hao đúng 1 bước gather (100 − 0.5/60), sắp theo id
  - snapshot quán tick 0 có stock đúng id, kind, fresh như file kho (dung sai ±0.01)
  - chạy lại gather cùng seed cho JSONL giống từng byte
Ghi: dock.json, dock-inputs.json, gather.jsonl, catch.json, quan.jsonl, smoke.md (lệnh, commit, kết quả).
Mã thoát: 0 đạt, 1 không đạt. Chỉ dùng thư viện chuẩn.
"""

import argparse
import datetime
import filecmp
import json
import os
import shlex
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLD = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100},
        {"id": "I3", "kind": "bong_sung", "fresh": 100}]  # v1.2 (TICKET-03): kho cá thể
FRESH_AFTER_1 = 100 - 0.5 / 60


def _rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        return "?"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase", default="phase-1", help="thư mục con trong docs/proof/ (mặc định phase-1)")
    ap.add_argument("--cmd", help="ghi đè headless_cmd (mặc định đọc game.contract.json)")
    a = ap.parse_args(argv)

    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        cmd_str = a.cmd or json.load(f)["headless_cmd"]
    cmd = shlex.split(cmd_str)
    out = os.path.join(ROOT, "docs", "proof", a.phase)
    # Kiểm cây làm việc TRƯỚC khi ghi bằng chứng, bỏ qua chính thư mục bằng chứng
    # (nếu kiểm sau, file do script vừa ghi sẽ bị tính nhầm là "thay đổi chưa commit").
    rel_out = os.path.relpath(out, ROOT).replace(os.sep, "/")
    commit = _git("rev-parse", "--short", "HEAD")
    dirty = " (có thay đổi chưa commit)" if _git("status", "--porcelain", "--", ".", f":(exclude){rel_out}") else ""
    os.makedirs(out, exist_ok=True)
    p = lambda name: os.path.join(out, name)

    with open(p("dock.json"), "w", encoding="utf-8") as f:
        json.dump({"gather": {"hold": HOLD, "random_fish": False, "monsters": []}}, f)
    with open(p("dock-inputs.json"), "w", encoding="utf-8") as f:
        json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
    for stale in ("catch.json", "gather.jsonl", "gather-rerun.jsonl", "quan.jsonl"):
        if os.path.exists(p(stale)):
            os.remove(p(stale))

    g_args = ["--mode", "gather", "--seed", "42", "--scenario", p("dock.json"), "--inputs", p("dock-inputs.json"),
              "--ticks", "1", "--out", p("gather.jsonl"), "--inventory-out", p("catch.json")]
    q_args = ["--mode", "quan", "--seed", "42", "--inventory", p("catch.json"), "--ticks", "0", "--out", p("quan.jsonl")]
    r_args = [x if x != p("gather.jsonl") else p("gather-rerun.jsonl") for x in g_args]
    r_args = [x for x in r_args if x not in ("--inventory-out", p("catch.json"))]

    checks, log = [], []

    def run(args):
        r = subprocess.run([*cmd, *args], cwd=ROOT, capture_output=True, text=True)
        rel = [os.path.relpath(x, ROOT).replace(os.sep, "/") if os.path.isabs(x) else x for x in args]
        log.append(f"$ {cmd_str} {' '.join(rel)}\n# exit {r.returncode}" + (f"\n# stderr: {r.stderr.strip()}" if r.stderr.strip() else ""))
        return r.returncode

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    gc = run(g_args)
    check("gather thoát mã 0", gc == 0, f"exit {gc}")
    qc = run(q_args) if gc == 0 else None
    check("quan thoát mã 0", qc == 0, f"exit {qc}")
    if gc == 0:
        ends = [r for r in _rows(p("gather.jsonl")) if r.get("type") == "event" and r.get("name") == "gather_end"]
        end = ends[0]["data"] if ends else {}
        check("gather_end reason = docked", end.get("reason") == "docked", str(end.get("reason")))
        inv = json.load(open(p("catch.json"), encoding="utf-8")) if os.path.exists(p("catch.json")) else None
        items = (inv or {}).get("items") or []
        ok = ([(i["id"], i["kind"]) for i in items] == [(h["id"], h["kind"]) for h in HOLD]
              and all(abs(i["fresh"] - FRESH_AFTER_1) < 1e-9 for i in items))
        check("file kho đúng id/kind, fresh hao 1 bước", ok, json.dumps(inv, ensure_ascii=False))
        ev_items = (end.get("inventory") or {}).get("items") or []
        # JSONL làm tròn 3 chữ số; file kho giữ float đầy đủ -> id/kind khớp chính xác, fresh dung sai ±0.01 (TICKET-03)
        same = (len(items) == len(ev_items) and all(a["id"] == b["id"] and a["kind"] == b["kind"]
                                                    and abs(a["fresh"] - b["fresh"]) <= 0.01 for a, b in zip(items, ev_items)))
        check("file kho = gather_end.inventory (id, kind; fresh ±0.01)", same)
        rc = run(r_args)
        check("chạy lại cùng seed giống từng byte", rc == 0 and filecmp.cmp(p("gather.jsonl"), p("gather-rerun.jsonl"), shallow=False))
        os.remove(p("gather-rerun.jsonl")) if os.path.exists(p("gather-rerun.jsonl")) else None
    if qc == 0:
        snap0 = next((r for r in _rows(p("quan.jsonl")) if r.get("type") == "snapshot" and r.get("tick") == 0), {})
        st = snap0.get("stock") or []
        file_items = (json.load(open(p("catch.json"), encoding="utf-8")) if os.path.exists(p("catch.json")) else {}).get("items", [])
        ok = (len(st) == len(file_items) and all(a["id"] == b["id"] and a["kind"] == b["kind"] and abs(a["fresh"] - b["fresh"]) <= 0.01
                                                 for a, b in zip(st, file_items)))
        check("quán tick 0 stock = file kho (id, kind, fresh)", ok, json.dumps(st, ensure_ascii=False))

    passed = all(ok for _, ok, _ in checks)
    md =[f"# Smoke hai tiến trình — {a.phase}", "",
          f"- Thời điểm: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
          f"- Commit: `{commit}`{dirty}",
          f"- Kết quả: **{'ĐẠT' if passed else 'CHƯA ĐẠT'}**", "",
          "| Kiểm tra | Kết quả | Chi tiết |", "|---|---|---|"]
    md += [f"| {n} | {'đạt' if ok else 'CHƯA ĐẠT'} | {d} |" for n, ok, d in checks]
    md += ["", "## Lệnh đã chạy", "", "```", *log, "```", "",
           "File đầu ra: `dock.json`, `dock-inputs.json`, `gather.jsonl`, `catch.json`, `quan.jsonl` (cùng thư mục).", ""]
    with open(p("smoke.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md))

    for n, ok, d in checks:
        print(f"[{'OK ' if ok else 'FAIL'}] {n}" + (f" — {d}" if d and not ok else ""))
    print(f"{'ĐẠT' if passed else 'CHƯA ĐẠT'} — bằng chứng: {os.path.relpath(p('smoke.md'), ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
