
import argparse
import json
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_mode(command, mode):
    is_day = mode == "day"
    ticks = 22200 if is_day else 60
    outputs = []
    passed = True

    with tempfile.TemporaryDirectory() as tmp:
        for number in (1, 2):
            output = Path(tmp) / f"{mode}-run{number}.jsonl"

            cmd = [
                *command,
                "--mode", mode,
                "--seed", "11",
                "--ticks", str(ticks),
                "--out", str(output),
            ]

            if is_day:
                cmd.extend([
                    "--days", "1",
                    "--snapshot-every", "600",
                ])

            start = time.perf_counter()

            try:
                result = subprocess.run(
                    cmd,
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=35,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                print(f"[FAIL] {mode} run {number}: {exc}")
                return False

            elapsed = time.perf_counter() - start

            if result.returncode != 0 or not output.is_file():
                print(
                    f"[FAIL] {mode} run {number}: "
                    f"exit={result.returncode}"
                )
                print(result.stderr.strip())
                return False

            data = output.read_bytes()
            outputs.append(data)

            if is_day:
                try:
                    last_line = [
                        line for line in data.splitlines()
                        if line.strip()
                    ][-1]
                    end = json.loads(last_line)
                except (IndexError, ValueError):
                    print("[FAIL] day: invalid JSONL end")
                    return False

                completed = (
                    isinstance(end, dict)
                    and end.get("type") == "end"
                    and end.get("mode") == "day"
                    and end.get("state") == "finished"
                    and end.get("reason") == "days_complete"
                    and end.get("days_completed") == 1
                    and type(end.get("ticks")) is int
                    and 0 < end["ticks"] <= 22200
                )

                speed_ok = elapsed <= 20.0

                print(
                    f"day run {number}: {elapsed:.3f}s, "
                    f"completed={completed}, "
                    f"speed_ok={speed_ok}"
                )

                if not completed or not speed_ok:
                    passed = False

    deterministic = (
        len(outputs) == 2
        and outputs[0] == outputs[1]
    )

    if deterministic:
        print(f"[PASS] {mode}: identical bytes")
    else:
        print(f"[FAIL] {mode}: output differs")

    return passed and deterministic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-python", action="store_true")
    parser.add_argument("--phase2", action="store_true")
    parser.add_argument(
        "--require-version",
        choices=["1.0", "1.1"],
    )
    args = parser.parse_args()

    contract = json.loads(
        (ROOT / "game.contract.json").read_text(
            encoding="utf-8"
        )
    )

    version = contract.get("contract_version", "missing")
    print(f"Contract version: {version}")

    if args.require_version and version != args.require_version:
        print(f"Required version: {args.require_version}")
        print("Phase 2 readiness: NOT READY")
        return 2

    if args.phase2 and version != "1.1":
        print("Phase 2 readiness: NOT READY")
        print("Reason: Contract v1.1 is required")
        return 2

    command = shlex.split(contract["headless_cmd"])

    if args.local_python:
        if not command or not command[0].lower().startswith("python"):
            print("ERROR: Cannot override launcher")
            return 1

        command[0] = sys.executable
        print("MODE: Local Python")
    else:
        print("MODE: Contract command")

    modes = ["gather", "quan"]

    if args.phase2:
        modes.append("day")

    all_passed = True

    for mode in modes:
        if not check_mode(command, mode):
            all_passed = False

    print("RESULT:", "PASS" if all_passed else "FAIL")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
