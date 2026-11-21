"""Run P1-04 tests and CLI scenarios, saving actual evidence (stdlib only).

From the repo root: python3 tools/verify_p1_04.py
Requires the contract's python3 command on PATH, including for black-box tests.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs" / "proof" / "phase-1"


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(ROOT / "tests"), str(ROOT))),
               PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    test_cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    tests = subprocess.run(test_cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, encoding="utf-8")
    (PROOF / "P1-04-tests.txt").write_text(tests.stdout, encoding="utf-8")
    print(tests.stdout.splitlines()[-4:])
    if tests.returncode:
        return tests.returncode

    cli_runs = []
    for label, mode, ticks, fixture in (
        ("default", "quan", 10800, False), ("fixture-a", "quan", 10800, True),
        ("fixture-b", "quan", 10800, True), ("gather", "gather", 600, False),
    ):
        out = PROOF / f"P1-04-{label}.jsonl"
        args = ["--mode", mode, "--seed", "42", "--ticks", str(ticks), "--out", str(out)]
        if fixture:
            args += ["--scenario", "tests/fixtures/p1_04_quan.json",
                     "--inputs", "tests/fixtures/p1_04_inputs.json", "--snapshot-every", "1"]
        command = [sys.executable, "-m", "chonoi.headless", *args]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8")
        cli_runs.append({"label": label, "args": args, "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(cli_runs[-1])
    a = (PROOF / "P1-04-fixture-a.jsonl").read_bytes()
    b = (PROOF / "P1-04-fixture-b.jsonl").read_bytes()
    if a != b:
        raise AssertionError("same seed/scenario/input produced different bytes")
    rows = [json.loads(line) for line in a.splitlines()]
    ev = [r for r in rows if r["type"] == "event"]
    expected = [(1, "cook_started"), (361, "dish_ready"), (361, "dish_picked"),
                (398, "served"), (998, "paid"), (10800, "quan_end")]
    if [(r["tick"], r["name"]) for r in ev] != expected:
        raise AssertionError(ev)
    if (rows[-1]["money"], rows[-1]["earned"], rows[-1]["reputation"], rows[-1]["score"]) != (72, 72, 3.2, 372):
        raise AssertionError(rows[-1])
    selected = [r for r in rows if r["type"] == "snapshot" and r["tick"] in (0, 1, 360, 361, 398, 998, 10800)]
    report = {"tests_exit_code": tests.returncode, "cli_runs": cli_runs,
              "deterministic_bytes": a == b, "sha256": hashlib.sha256(a).hexdigest(),
              "events": ev, "snapshots": selected, "end": rows[-1]}
    (PROOF / "P1-04-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P1-04: tests and 4 headless runs passed; money=72, reputation=3.2, score=372.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
