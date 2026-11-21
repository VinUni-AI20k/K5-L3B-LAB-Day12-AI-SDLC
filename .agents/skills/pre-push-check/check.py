#!/usr/bin/env python3
"""Kiểm trước khi đẩy (skill pre-push-check). Chạy từ bất kỳ đâu trong repo:

    python3 .agents/skills/pre-push-check/check.py              # đủ bước
    python3 .agents/skills/pre-push-check/check.py --no-tests   # bỏ unittest (chỉ khi sửa lặp nhanh)

Thoát 0 khi mọi bước bắt buộc đạt, 1 nếu có bước FAIL. In dòng tóm tắt để dán vào mô tả commit.
Chỉ dùng thư viện chuẩn; chạy được trên macOS/Linux/Windows (Python >= 3.9).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DAY_TICKS = 22200     # một Ngày không pause dài tối đa 22.200 tick (TICKET-02 mục 2)
DAY_LIMIT_S = 20.0    # headless một Ngày phải chạy <= 20 s trên máy chấm
BIG_FILE = 10 * 1024 * 1024
SENSITIVE = [r"(^|/)\.env($|\.)", r"\.pem$", r"\.key$", r"(^|/)credentials?\.json$",
             r"(^|/)\.claude/settings\.local\.json$", r"(^|/)__pycache__/", r"\.pyc$"]
TOKEN_RE = r"(sk-ant-[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16})"

OK, WARN, FAIL, SKIP = "OK", "WARN", "FAIL", "SKIP"


def child_env():
    e = dict(os.environ)
    e["PYTHONPATH"] = os.pathsep.join(["tests", "."])
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def run(cmd, timeout=900, cwd=None):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd or ROOT, env=child_env(), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p, time.time() - t0


def tail(text, n=3):
    lines = [l for l in (text or "").strip().splitlines() if l.strip()]
    return " | ".join(lines[-n:])


def step_contract():
    code = ("from chonoi.contract import load_contract; c = load_contract(); "
            "print(c.get('contract_version'), c.get('team_size'))")
    p, _ = run([sys.executable, "-c", code], timeout=60)
    if p.returncode:
        return FAIL, "game.contract.json không hợp lệ: " + tail(p.stderr, 1), None
    ver, size = (p.stdout.split() + ["?", "?"])[:2]
    return OK, f"game.contract.json hợp lệ (contract_version {ver}, team_size {size})", f"contract v{ver}"


def step_team():
    script = os.path.join(ROOT, "tools", "check_team.py")
    if not os.path.exists(script):
        return SKIP, "không có tools/check_team.py", None
    p, _ = run([sys.executable, script], timeout=60)
    if p.returncode:
        lines = [l.strip() for l in (p.stdout + "\n" + p.stderr).splitlines() if l.strip()]
        problems = [l.lstrip("- ").strip() for l in lines if l.startswith("-")] or lines[-2:]
        return WARN, "TEAM.md chưa đạt: " + "; ".join(problems), None
    return OK, "TEAM.md đạt", None


def step_tests(skip):
    if skip:
        return SKIP, "bỏ qua theo --no-tests (KHÔNG dùng cho lần chạy cuối trước khi push)", None
    p, dt = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    out = p.stdout + p.stderr
    m = re.search(r"Ran (\d+) tests?", out)
    ran = m.group(1) if m else "?"
    if p.returncode == 0 and re.search(r"^OK", out, re.M):
        return OK, f"{ran} test, OK ({dt:.0f} s)", f"unittest {ran} OK"
    return FAIL, f"{ran} test, HỎNG: " + tail(out, 2), f"unittest {ran} HỎNG"


def step_headless():
    tmp = tempfile.mkdtemp(prefix="chonoi-prepush-")
    try:
        cases = [("gather", ["--ticks", "600"]), ("quan", ["--ticks", "600"]),
                 ("day", ["--days", "1", "--ticks", str(DAY_TICKS)])]
        notes, bad, day_s = [], [], None
        for mode, extra in cases:
            out = os.path.join(tmp, mode + ".jsonl")
            cmd = [sys.executable, "-m", "chonoi.headless", "--mode", mode, "--seed", "1", *extra, "--out", out]
            p, dt = run(cmd, timeout=120)
            last = None
            if p.returncode == 0 and os.path.exists(out):
                with open(out, encoding="utf-8") as f:
                    lines = [l for l in f if l.strip()]
                last = json.loads(lines[-1]) if lines else None
            if p.returncode != 0 or not last or last.get("type") != "end":
                bad.append(f"{mode} (mã {p.returncode}: {tail(p.stderr, 1) or 'không có dòng end'})")
                continue
            notes.append(f"{mode} {dt:.1f}s")
            if mode == "day":
                day_s = dt
                if dt > DAY_LIMIT_S:
                    bad.append(f"day chạy {dt:.1f} s > {DAY_LIMIT_S:.0f} s")
        if bad:
            return FAIL, "; ".join(bad), "headless HỎNG"
        return OK, "exit 0 + dòng end: " + ", ".join(notes), f"headless gather/quan/day exit 0, 1 Ngày {day_s:.1f} s ≤ {DAY_LIMIT_S:.0f} s"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def step_client_js():
    src = os.path.join(ROOT, "client", "src")
    if not os.path.isdir(src):
        return SKIP, "không có client/src", None
    node = shutil.which("node")
    if not node:
        return SKIP, "máy không có node — bỏ kiểm cú pháp JS (nhớ chơi thử trên trình duyệt)", None
    files = sorted(f for f in os.listdir(src) if f.endswith(".js"))
    tmp = tempfile.mkdtemp(prefix="chonoi-js-")
    try:
        bad = []
        for f in files:
            copy = os.path.join(tmp, f[:-3] + ".mjs")   # .mjs để node hiểu là ES module
            shutil.copyfile(os.path.join(src, f), copy)
            p, _ = run([node, "--check", copy], timeout=60)
            if p.returncode:
                err = [l.strip() for l in p.stderr.splitlines() if "Error" in l]
                bad.append(f"{f}: {err[0] if err else tail(p.stderr, 1)}")
        if bad:
            return FAIL, "lỗi cú pháp: " + "; ".join(bad), "client JS HỎNG"
        return OK, f"{len(files)} file client/src/*.js không lỗi cú pháp", f"client JS {len(files)} file OK"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def step_git():
    p, _ = run(["git", "ls-files"], timeout=60)
    if p.returncode:
        return SKIP, "không phải repo git", None
    tracked = p.stdout.splitlines()
    leaked = [f for f in tracked if any(re.search(rx, f) for rx in SENSITIVE)]
    g, _ = run(["git", "grep", "-nIE", TOKEN_RE, "--", ".", ":!client/assets"], timeout=60)
    tokens = [l.split(":", 2)[0] + ":" + l.split(":", 2)[1] for l in g.stdout.splitlines() if l.count(":") >= 2]
    big = [f for f in tracked if os.path.isfile(os.path.join(ROOT, f)) and os.path.getsize(os.path.join(ROOT, f)) > BIG_FILE]
    s, _ = run(["git", "status", "--porcelain"], timeout=60)
    dirty = len([l for l in s.stdout.splitlines() if l.strip()])
    if leaked or tokens:
        return FAIL, "file/chuỗi nhạy cảm đang được track: " + ", ".join(leaked + tokens), None
    if big:
        return WARN, "file > 10 MB: " + ", ".join(big), None
    return OK, f"không có file nhạy cảm/token; {dirty} file đang thay đổi chưa commit", None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Kiểm trước khi đẩy (pre-push-check)")
    ap.add_argument("--no-tests", action="store_true", help="bỏ unittest (chỉ khi sửa lặp nhanh)")
    args = ap.parse_args()

    steps = [("contract", step_contract), ("team", step_team), ("unittest", lambda: step_tests(args.no_tests)),
             ("headless", step_headless), ("client-js", step_client_js), ("git", step_git)]
    print("== Kiểm trước khi đẩy (pre-push-check) ==")
    results, summary = [], []
    for name, fn in steps:
        try:
            status, msg, short = fn()
        except subprocess.TimeoutExpired as e:
            status, msg, short = FAIL, f"quá thời gian ({e.timeout} s)", f"{name} quá thời gian"
        except Exception as e:  # một bước hỏng không được làm mất kết quả các bước khác
            status, msg, short = FAIL, f"lỗi khi kiểm: {e!r}", f"{name} lỗi"
        results.append(status)
        if short:
            summary.append(short)
        print(f"[{status:<4}] {name:<9} {msg}", flush=True)

    failed = results.count(FAIL)
    print()
    print("Kiểm trước khi đẩy: " + "; ".join(summary) + (" — CÓ BƯỚC HỎNG" if failed else ""))
    if failed:
        print(f"\n{failed} bước FAIL → KHÔNG push. Xem dòng [FAIL] ở trên.")
    else:
        print("\nĐạt. Nếu có đổi client/: chơi thử trên trình duyệt trước khi push (xem SKILL.md, bước tay).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
