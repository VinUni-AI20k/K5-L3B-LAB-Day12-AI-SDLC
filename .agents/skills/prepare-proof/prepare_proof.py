import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def execute(cmd, *, timeout=60, env=None):
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        code, stdout, stderr = (
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
    except subprocess.TimeoutExpired:
        code, stdout, stderr = 124, "", f"TIMEOUT after {timeout}s"
    except OSError as exc:
        code, stdout, stderr = 1, "", f"Cannot start process: {exc}"

    return {
        "code": code,
        "stdout": stdout,
        "stderr": stderr,
        "elapsed": time.perf_counter() - start,
    }


def write_log(path, cmd, result):
    path.write_text(
        f"Command argv: {cmd!r}\n"
        f"Exit code: {result['code']}\n"
        f"Duration: {result['elapsed']:.3f}s\n"
        f"STDOUT:\n{result['stdout']}\n"
        f"STDERR:\n{result['stderr']}\n",
        encoding="utf-8",
    )


def day_completed(data):
    """Require a completed day event as the final non-empty JSONL line."""
    if not data:
        return False
    try:
        last_line = [line for line in data.splitlines() if line.strip()][-1]
        end = json.loads(last_line)
    except (IndexError, ValueError, TypeError):
        return False
    return (
        isinstance(end, dict)
        and end.get("type") == "end"
        and end.get("mode") == "day"
        and end.get("state") == "finished"
        and end.get("reason") == "days_complete"
        and type(end.get("days_completed")) is int
        and end["days_completed"] == 1
        and type(end.get("ticks")) is int
        and 0 < end["ticks"] <= 22200
    )


def run_mode(command, out_dir, mode, report):
    is_day = mode == "day"
    ticks = 22200 if is_day else 60
    records = []

    for number in (1, 2):
        output = out_dir / f"{mode}-run{number}.jsonl"
        cmd = [
            *command,
            "--mode", mode,
            "--seed", "11",
            "--ticks", str(ticks),
            "--out", str(output),
        ]
        if is_day:
            cmd += ["--days", "1", "--snapshot-every", "600"]

        result = execute(cmd, timeout=35)
        write_log(out_dir / f"{mode}-run{number}.log", cmd, result)
        data = output.read_bytes() if output.is_file() else None
        complete = day_completed(data) if is_day else True
        fast_enough = result["elapsed"] <= 20.0 if is_day else True
        success = (
            result["code"] == 0
            and data is not None
            and len(data) > 0
            and complete
            and fast_enough
        )
        records.append({
            "result": result,
            "data": data,
            "completed": complete,
            "speed_ok": fast_enough,
            "success": success,
        })

        if is_day:
            print(
                f"day run {number}: {'PASS' if success else 'FAIL'} "
                f"({result['elapsed']:.3f}s)"
            )

    deterministic = (
        all(item["data"] is not None for item in records)
        and records[0]["data"] == records[1]["data"]
    )
    passed = all(item["success"] for item in records) and deterministic

    if is_day:
        report.extend([
            "", "## Phase 2 — Full Day", "",
            "| Run | Duration | Completed | Within 20s | Exit | Result |",
            "|---|---|---|---|---|---|",
        ])
        for number, record in enumerate(records, start=1):
            result = record["result"]
            report.append(
                f"| {number} | {result['elapsed']:.3f}s | "
                f"{record['completed']} | {record['speed_ok']} | "
                f"{result['code']} | "
                f"{'PASS' if record['success'] else 'FAIL'} |"
            )
        report.extend([
            "", f"- Day determinism: {'PASS' if deterministic else 'FAIL'}",
        ])
        for number, record in enumerate(records, start=1):
            if record["data"] is not None:
                report.append(
                    f"- Day run {number} SHA-256: "
                    f"`{sha256(record['data'])}`"
                )
    else:
        # The caller prints both gather/quan rows consecutively, then hashes.
        row = (
            f"| {mode} | {records[0]['result']['code']} | "
            f"{records[1]['result']['code']} | "
            f"{'PASS' if passed else 'FAIL'} |"
        )
        hashes = [
            f"- {mode} run {number} SHA-256: `{sha256(record['data'])}`"
            for number, record in enumerate(records, start=1)
            if record["data"] is not None
        ]
        print(f"{mode}: {'PASS' if passed else 'FAIL'}")
        return passed, row, hashes

    return passed, None, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2", action="store_true")
    parser.add_argument(
        "--local-python", action="store_true",
        help="Use the current Python executable instead of the contract launcher",
    )
    args = parser.parse_args()

    try:
        contract = json.loads(
            (ROOT / "game.contract.json").read_text(encoding="utf-8")
        )
        launcher = shlex.split(contract["headless_cmd"])
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: Cannot read Test Contract: {exc}")
        return 2

    version = contract.get("contract_version", "missing")
    print(f"Contract version: {version}")
    if args.phase2 and version != "1.1":
        print("Phase 2 readiness: NOT READY (Contract v1.1 required)")
        return 2

    if not launcher:
        print("ERROR: Empty headless_cmd")
        return 2
    if args.local_python:
        if not Path(launcher[0]).name.lower().startswith("python"):
            print("ERROR: Cannot override a non-Python launcher")
            return 2
        launcher[0] = sys.executable
        print("MODE: Local Python (not the exact contract launcher)")
    else:
        print("MODE: Contract command")

    phase = "phase-2" if args.phase2 else "phase-1"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out_dir = ROOT / "docs" / "proof" / phase / "harness" / stamp
    out_dir.mkdir(parents=True, exist_ok=False)

    report = [
        f"# Harness Verification — {'Phase 2' if args.phase2 else 'Phase 1'}",
        "", f"Run: `{stamp}`", "",
        f"- Contract version: `{version}`",
        f"- Launcher: `{'local-python' if args.local_python else 'contract'}`",
        "", "## Unit tests", "",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(["tests", "."])
    test_cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    test_result = execute(test_cmd, timeout=180, env=env)
    write_log(out_dir / "test-output.txt", test_cmd, test_result)
    test_pass = test_result["code"] == 0
    report.extend([
        f"- Status: {'PASS' if test_pass else 'FAIL'}",
        "- Evidence: `test-output.txt`", "",
        "## Headless determinism", "",
        "| Mode | Run 1 exit | Run 2 exit | Determinism and success |",
        "|---|---|---|---|",
    ])

    overall = test_pass
    hashes = []
    for mode in ("gather", "quan"):
        passed, row, mode_hashes = run_mode(launcher, out_dir, mode, report)
        report.append(row)
        hashes.extend(mode_hashes)
        overall = overall and passed

    report.extend(["", "### SHA-256", "", *hashes])
    if args.phase2:
        passed, _, _ = run_mode(launcher, out_dir, "day", report)
        overall = overall and passed

    report.extend([
        "", "## Overall result", "",
        "**PASS**" if overall else "**FAIL**", "",
        (
            "Note: Harness PASS does not prove every Phase 2 AC."
            if args.phase2
            else "Note: Harness PASS does not prove every PRD-0 AC."
        ),
        "QA must map each AC to appropriate evidence.",
    ])
    (out_dir / "report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )

    print("Unit tests:", "PASS" if test_pass else "FAIL")
    print("Overall:", "PASS" if overall else "FAIL")
    print("Evidence:", out_dir)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
