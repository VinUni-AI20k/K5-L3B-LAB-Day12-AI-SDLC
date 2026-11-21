"""Chạy kiểm chứng Phase 1 và lưu văn bản để đính kèm vào ma trận."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def verify_tests():
    env = os.environ.copy()
    pythonpath = [str(ROOT / "tests"), str(ROOT)]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    return completed.stdout, completed.returncode


def verify_headless(seed, ticks):
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    command = shlex.split(contract["headless_cmd"])
    lines = [f"headless_cmd: {contract['headless_cmd']}", f"seed={seed} ticks={ticks}"]
    failed = False
    with tempfile.TemporaryDirectory() as temp:
        for mode in ("gather", "quan"):
            outputs = [Path(temp) / f"{mode}-{run}.jsonl" for run in (1, 2)]
            for output in outputs:
                subprocess.run(
                    [*command, "--mode", mode, "--seed", str(seed), "--ticks", str(ticks),
                     "--out", str(output)],
                    cwd=ROOT, check=True,
                )
            first, second = (output.read_bytes() for output in outputs)
            identical = first == second
            failed |= not identical
            lines.append(f"{mode}: identical={identical} bytes={len(first)}")
            for run, replay in enumerate((first, second), 1):
                end = json.loads(replay.splitlines()[-1])
                lines.append(
                    f"  run={run} sha256={hashlib.sha256(replay).hexdigest()} "
                    f"end={end['reason']} ticks={end['ticks']}"
                )
    return "\n".join(lines) + "\n", int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    tests = commands.add_parser("tests", help="Chạy toàn bộ unittest.")
    tests.add_argument("--out", type=Path, required=True, help="Đường dẫn lưu log.")
    headless = commands.add_parser("headless", help="Chạy hai lượt mỗi mode và so JSONL theo byte.")
    headless.add_argument("--out", type=Path, required=True, help="Đường dẫn lưu báo cáo.")
    headless.add_argument("--seed", type=int, default=1)
    headless.add_argument("--ticks", type=int, default=600)
    args = parser.parse_args()

    try:
        report, status = verify_tests() if args.command == "tests" else verify_headless(args.seed, args.ticks)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8", newline="\n")
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f"{error}\n")
    print(report, end="")
    return status


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())
