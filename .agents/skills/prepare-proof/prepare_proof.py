
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
OUT = ROOT / "docs" / "proof" / "phase-1" / "harness" / STAMP
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd):
    try:
        return subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            errors="replace",
        )
    except OSError as exc:
        class Failure:
            returncode = 1
            stdout = ""
            stderr = str(exc)
        return Failure()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lines = [
        "# Harness Verification — Phase 1",
        "",
        f"Run: `{STAMP}`",
        "",
        "## Unit tests",
    ]
    all_passed = True

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(["tests", "."])

    test_cmd = [
        sys.executable,
        "-m", "unittest",
        "discover", "-s", "tests", "-v",
    ]

    try:
        tests = subprocess.run(
            test_cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
        )
        test_log = tests.stdout + "\n" + tests.stderr
        test_pass = tests.returncode == 0
    except OSError as exc:
        test_log = str(exc)
        test_pass = False

    (OUT / "test-output.txt").write_text(
        test_log, encoding="utf-8"
    )

    lines += [
        f"- Status: {'PASS' if test_pass else 'FAIL'}",
        "- Evidence: `test-output.txt`",
        "",
        "## Headless determinism",
        "",
        "| Mode | Run 1 | Run 2 | Determinism |",
        "|---|---|---|---|",
    ]

    all_passed &= test_pass

    contract = json.loads(
        (ROOT / "game.contract.json").read_text(
            encoding="utf-8"
        )
    )
    base_cmd = shlex.split(contract["headless_cmd"])

    for mode in ("gather", "quan"):
        outputs = []
        codes = []

        for number in (1, 2):
            path = OUT / f"{mode}-run{number}.jsonl"

            cmd = [
                *base_cmd,
                "--mode", mode,
                "--seed", "11",
                "--ticks", "60",
                "--out", str(path),
            ]

            result = run(cmd)
            codes.append(result.returncode)
            outputs.append(path)

            log_path = OUT / f"{mode}-run{number}.log"
            log_path.write_text(
                f"Exit code: {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n",
                encoding="utf-8",
            )

        passed = (
            codes == [0, 0]
            and all(path.is_file() for path in outputs)
            and outputs[0].read_bytes()
                == outputs[1].read_bytes()
        )

        all_passed &= passed

        status = "PASS" if passed else "FAIL"

        lines.append(
            f"| {mode} | {codes[0]} | {codes[1]} | {status} |"
        )

        if all(path.is_file() for path in outputs):
            lines.append(
                f"\n- {mode} SHA-256 run 1: "
                f"`{sha256(outputs[0])}`"
            )
            lines.append(
                f"- {mode} SHA-256 run 2: "
                f"`{sha256(outputs[1])}`"
            )

        print(f"{mode}: {status}")

    lines += [
        "",
        "## Overall result",
        "",
        "**PASS**" if all_passed else "**FAIL**",
        "",
        "Note: This report does not prove every PRD-0 AC.",
        "QA must map each AC to suitable evidence.",
    ]

    (OUT / "report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("Unit tests:", "PASS" if test_pass else "FAIL")
    print("Overall:", "PASS" if all_passed else "FAIL")
    print("Evidence:", OUT)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
