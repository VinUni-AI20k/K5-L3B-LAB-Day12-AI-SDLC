#!/usr/bin/env python3
"""Kiểm chứng tại tag (skill verify-tag): xuất mã của tag ra thư mục tạm sạch, chạy test + headless ở đó.

    python3 .agents/skills/verify-tag/verify_tag.py                   # mọi tag phase-* và v*
    python3 .agents/skills/verify-tag/verify_tag.py phase-3 phase-4   # chỉ các tag này
    python3 .agents/skills/verify-tag/verify_tag.py --offline         # không hỏi remote

In bảng Markdown để dán vào docs/verification/phase-n.md. Thoát 1 nếu có tag hỏng hoặc lệch remote.
Chỉ dùng thư viện chuẩn; chạy được trên macOS/Linux/Windows (Python >= 3.9).
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DAY_TICKS = 22200
DAY_LIMIT_S = 20.0


def child_env():
    e = dict(os.environ)
    e["PYTHONPATH"] = os.pathsep.join(["tests", "."])
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def run(cmd, cwd, timeout=900, binary=False):
    t0 = time.time()
    if binary:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
    else:
        p = subprocess.run(cmd, cwd=cwd, env=child_env(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    return p, time.time() - t0


def git(*args):
    p, _ = run(["git", *args], cwd=ROOT, timeout=60)
    if p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def natural_key(tag):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", tag)]


def remote_tags():
    """{tag: commit} trên origin; None nếu không hỏi được (mất mạng / không có remote)."""
    try:
        p, _ = run(["git", "ls-remote", "--tags", "origin"], cwd=ROOT, timeout=30)
    except subprocess.TimeoutExpired:
        return None
    if p.returncode:
        return None
    tags = {}
    for line in p.stdout.splitlines():
        sha, ref = line.split("\t")
        name = ref.replace("refs/tags/", "")
        if name.endswith("^{}"):           # tag có chú thích: dòng ^{} là commit thật
            tags[name[:-3]] = sha
        else:
            tags.setdefault(name, sha)
    return tags


def export(tag, dest):
    p, _ = run(["git", "archive", "--format=tar", tag], cwd=ROOT, timeout=120, binary=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode("utf-8", "replace").strip())
    with tarfile.open(fileobj=io.BytesIO(p.stdout)) as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(dest, filter="data")
        else:
            tf.extractall(dest)


def version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).split(".")[:2])
    except ValueError:
        return (0, 0)


def check_tag(tag):
    tmp = tempfile.mkdtemp(prefix="chonoi-tag-")
    res = {"tag": tag, "ok": True, "tests": "?", "headless": "?", "version": "?"}
    try:
        export(tag, tmp)
        try:
            with open(os.path.join(tmp, "game.contract.json"), encoding="utf-8") as f:
                res["version"] = json.load(f).get("contract_version", "?")
        except (OSError, ValueError):
            pass

        p, dt = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=tmp)
        out = p.stdout + p.stderr
        m = re.search(r"Ran (\d+) tests?", out)
        ran = m.group(1) if m else "?"
        if p.returncode == 0 and re.search(r"^OK", out, re.M):
            res["tests"] = f"{ran} OK ({dt:.0f} s)"
        else:
            res["ok"] = False
            fail = re.search(r"^FAILED \(.*\)", out, re.M)
            res["tests"] = f"{ran} HỎNG" + (f" — {fail.group(0)}" if fail else "")

        cases = [("gather", ["--ticks", "600"])]
        if version_tuple(res["version"]) >= (1, 1):
            cases.append(("day", ["--days", "1", "--ticks", str(DAY_TICKS)]))
        parts = []
        for mode, extra in cases:
            jl = os.path.join(tmp, f"_verify_{mode}.jsonl")
            p, dt = run([sys.executable, "-m", "chonoi.headless", "--mode", mode, "--seed", "1", *extra,
                         "--out", jl], cwd=tmp, timeout=120)
            ended = False
            if p.returncode == 0 and os.path.exists(jl):
                with open(jl, encoding="utf-8") as f:
                    lines = [l for l in f if l.strip()]
                ended = bool(lines) and json.loads(lines[-1]).get("type") == "end"
            if not ended or (mode == "day" and dt > DAY_LIMIT_S):
                res["ok"] = False
                parts.append(f"{mode} HỎNG (mã {p.returncode}, {dt:.1f} s)")
            else:
                parts.append(f"{mode} {dt:.1f} s")
        res["headless"] = ", ".join(parts)
    except Exception as e:  # một tag hỏng không làm dừng các tag khác
        res["ok"] = False
        res["tests"] = f"lỗi: {e}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Kiểm chứng tại tag (verify-tag)")
    ap.add_argument("tags", nargs="*", help="tag cần kiểm (mặc định: mọi tag phase-* và v*)")
    ap.add_argument("--offline", action="store_true", help="không hỏi remote")
    args = ap.parse_args()

    tags = args.tags or sorted((t for t in git("tag", "-l").splitlines() if re.match(r"^(phase-\d+|v\d)", t)),
                               key=natural_key)
    if not tags:
        print("Không có tag phase-* hoặc v* nào.")
        return 1
    remote = None if args.offline else remote_tags()

    rows, bad = [], 0
    for tag in tags:
        try:
            sha = git("rev-list", "-n1", tag)
        except RuntimeError as e:
            print(f"[FAIL] {tag}: {e}")
            bad += 1
            continue
        when = git("for-each-ref", f"refs/tags/{tag}", "--format=%(creatordate:iso)")
        print(f"... đang kiểm {tag} ({sha[:7]})", flush=True)
        r = check_tag(tag)
        if remote is None:
            pushed = "? (không hỏi được remote)"
        elif tag not in remote:
            pushed, r["ok"] = "CHƯA đẩy", False
        elif remote[tag] != sha:
            pushed, r["ok"] = f"LỆCH (remote {remote[tag][:7]})", False
        else:
            pushed = "đã đẩy"
        bad += 0 if r["ok"] else 1
        rows.append(f"| `{tag}` | `{sha[:7]}` | {when} | {r['version']} | {pushed} | {r['tests']} | {r['headless']} | "
                    f"{'Đạt' if r['ok'] else '**HỎNG**'} |")

    print()
    print(f"Kiểm chứng tại tag — chạy lúc {time.strftime('%Y-%m-%d %H:%M')} bằng "
          f"`python3 .agents/skills/verify-tag/verify_tag.py` (mã của tag xuất bằng `git archive`, không lẫn working tree):")
    print()
    print("| Tag | Commit | Thời điểm tag | Contract | Remote | unittest | Headless (seed 1) | Kết quả |")
    print("|---|---|---|---|---|---|---|---|")
    for row in rows:
        print(row)
    print()
    print(f"{len(tags) - bad}/{len(tags)} tag đạt." + (" Có tag HỎNG — xem bảng." if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
