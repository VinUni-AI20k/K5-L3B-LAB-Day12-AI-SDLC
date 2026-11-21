
import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-python", action="store_true")
    args = parser.parse_args()

    contract = json.loads(
        (ROOT / "game.contract.json").read_text(encoding="utf-8")
    )

    command = shlex.split(contract["headless_cmd"])

    if args.local_python:
        if not command or not command[0].lower().startswith("python"):
            print("ERROR: Cannot override a non-Python launcher")
            return 1
        command[0] = sys.executable
        print("MODE: Local Python (not exact contract launcher)")
    else:
        print("MODE: Contract command")

    all_passed = True

    for mode in ("gather", "quan"):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [
                Path(tmp) / "run1.jsonl",
                Path(tmp) / "run2.jsonl",
            ]

            results = []

            for output in outputs:
                cmd = [
                    *command,
                    "--mode", mode,
                    "--seed", "11",
                    "--ticks", "60",
                    "--out", str(output),
                ]

                try:
                    result = subprocess.run(
                        cmd,
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                except OSError as exc:
                    print(f"[FAIL] {mode}: {exc}")
                    all_passed = False
                    break

                if result.returncode != 0 or not output.is_file():
                    print(
                        f"[FAIL] {mode}: "
                        f"exit={result.returncode}"
                    )
                    print(result.stderr.strip())
                    all_passed = False
                    break

                results.append(output.read_bytes())

            if len(results) == 2:
                if results[0] == results[1]:
                    print(f"[PASS] {mode}: identical bytes")
                else:
                    print(f"[FAIL] {mode}: output differs")
                    all_passed = False

    print("RESULT:", "PASS" if all_passed else "FAIL")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
