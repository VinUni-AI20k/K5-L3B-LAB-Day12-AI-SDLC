"""Tiến độ từng người: python3 tools/team_progress.py

Fetch remote, in bảng: nhánh, người, commit gần nhất, số commit vượt main, thời gian.
Dùng để cập nhật standup mà không phải mở GitHub.
"""

import subprocess
import sys

ROOT = "."
BRANCHES = [
    ("feat/cao-minh", "Cao Minh"),
    ("feat/nhat-minh", "Nhật Minh"),
    ("feat/quang-vinh", "Vinh"),
    ("feat/van-minh", "Văn Minh"),
    ("feat/duc-minh", "Đức Minh"),
]


def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def main():
    git("fetch", "--prune", "origin")
    base = "336e0f4"  # commit kickoff Phase 1; commit trước đó là của giảng viên
    print(f"{'nhánh':22} {'người':10} {'trên nhánh':>10}  {'trạng thái':12} {'commit gần nhất'}")
    print("-" * 92)
    total = 0
    for branch, who in BRANCHES:
        ref = f"origin/{branch}"
        if not git("rev-parse", "--verify", ref):
            print(f"{branch:22} {who:10} {'—':>9}  (chưa có trên remote)")
            continue
        n = git("rev-list", "--count", f"{base}..{ref}") or "0"
        total += int(n)
        merged = subprocess.run(["git", "merge-base", "--is-ancestor", ref, "origin/main"],
                                cwd=ROOT).returncode == 0
        state = "chưa bắt đầu" if int(n) == 0 else ("đã merge" if merged else "đang làm")
        log = git("log", "-1", "--format=%an|%ar|%s", ref) if int(n) else ""
        print(f"{branch:22} {who:10} {n:>10}  {state:12} {log}")
    print("-" * 92)
    print(f"Tổng commit của nhóm (sau kickoff): {total}  ·  main: {git('log', '-1', '--format=%h %s', 'origin/main')}")
    print(f"Từ commit gốc của giảng viên: {git('rev-list', '--count', f'{base}..origin/main')} commit trên main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
