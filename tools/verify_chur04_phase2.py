"""Bằng chứng lát chur04: chạy trên bản sao v1.1, không thay manifest chung.

    python tools/verify_chur04_phase2.py

Fixture tắt cá tự động vì engine Gather v1.1 thuộc lát khác. Không xác nhận
DoD toàn nhóm. Toàn bộ test và các tiến trình CLI đều dùng nguồn hiện tại.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    import helpers
    from test_chur04_phase2 import phase2_contract, quick_scenario

    out = ROOT / "docs/proof/phase-2/chur04"
    out.mkdir(parents=True, exist_ok=True)
    command = helpers.headless_cmd()
    local_launcher = os.name == "nt" and command[:3] == ["python3", "-m", "chonoi.headless"]
    if local_launcher:
        command[0] = sys.executable
    with (out / "tests.txt").open("w", encoding="utf-8") as stream:
        stream.write(f"Windows launcher replacement for legacy tests: {local_launcher}\n")
        with patch.object(helpers, "headless_cmd", return_value=command):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover("tests"))
    summary = {"tests_run": result.testsRun, "tests_passed": result.wasSuccessful(),
               "legacy_tests_local_python": local_launcher, "scope": "chur04 backend; random_fish=false, no monster validation"}
    if not result.wasSuccessful():
        write_json(out / "summary.json", summary)
        print("FAIL: xem", out / "tests.txt")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "chonoi", work / "chonoi", ignore=shutil.ignore_patterns("__pycache__", "web"))
        fixture = phase2_contract()
        write_json(work / "game.contract.json", fixture)
        write_json(out / "fixture-contract.json", fixture)

        def cli(label, *args):
            command = [sys.executable, "-m", "chonoi.headless", *args]
            started = time.perf_counter()
            process = subprocess.run(command, cwd=work, capture_output=True, timeout=30)
            elapsed = time.perf_counter() - started
            (out / f"{label}.log").write_text(f"Command: python -m chonoi.headless {' '.join(args)}\n"
                f"Exit: {process.returncode}\nElapsed seconds: {elapsed:.6f}\n"
                + process.stderr.decode("utf-8", errors="replace"), encoding="utf-8")
            if process.returncode:
                raise RuntimeError(f"{label}: exit {process.returncode}; xem {out / (label + '.log')}")
            return elapsed

        scenario = quick_scenario(money=200, earned=200)
        frames = {"frames": [{"tick": 2, "buy": "oxygen", "shop_done": True},
                             {"tick": 3, "shop_done": False}, {"tick": 5, "shop_done": True}]}
        write_json(out / "day-scenario.json", scenario)
        write_json(out / "day-inputs.json", frames)
        outputs = []
        for number in (1, 2):
            path = out / f"day-run{number}.txt"
            cli(f"day-run{number}", "--mode", "day", "--days", "2", "--seed", "7", "--ticks", "20",
                "--scenario", str(out / "day-scenario.json"), "--inputs", str(out / "day-inputs.json"), "--out", str(path))
            outputs.append(path.read_bytes())
        summary["day_deterministic"] = outputs[0] == outputs[1]
        summary["day_sha256"] = hashlib.sha256(outputs[0]).hexdigest()
        summary["day_end"] = json.loads(outputs[0].splitlines()[-1])

        full = {"gather": {"random_fish": False}, "quan": {"random_customers": False}}
        write_json(out / "full-day-scenario.json", full)
        seconds = cli("full-day", "--mode", "day", "--days", "1", "--seed", "7", "--ticks", "22200",
                      "--scenario", str(out / "full-day-scenario.json"), "--snapshot-every", "600", "--out", str(out / "full-day.txt"))
        summary["full_day_seconds"] = round(seconds, 6)
        summary["full_day_end"] = json.loads((out / "full-day.txt").read_bytes().splitlines()[-1])

        write_json(out / "dock-scenario.json", {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}})
        write_json(out / "dock-inputs.json", {"frames": [{"tick": 0, "interact": True}]})
        cli("integration-gather", "--mode", "gather", "--seed", "42", "--ticks", "1", "--scenario", str(out / "dock-scenario.json"),
            "--inputs", str(out / "dock-inputs.json"), "--inventory-out", str(out / "inventory.json"), "--out", str(out / "integration-gather.txt"))
        cli("integration-quan", "--mode", "quan", "--seed", "42", "--ticks", "0", "--inventory", str(out / "inventory.json"),
            "--out", str(out / "integration-quan.txt"))
        inventory = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
        quan = json.loads((out / "integration-quan.txt").read_bytes().splitlines()[0])
        summary["inventory_handoff"] = quan["stock"] == inventory["items"] == {"bong_sung": 2, "ca_loc": 1}

    passed = (summary["day_deterministic"] and summary["inventory_handoff"] and seconds <= 20
              and summary["full_day_end"]["reason"] == "days_complete"
              and summary["full_day_end"]["sim_tick"] == 22200)
    summary["passed"] = passed
    write_json(out / "summary.json", summary)
    print(f"Tests: {result.testsRun}, {'PASS' if result.wasSuccessful() else 'FAIL'}")
    print("Day determinism:", summary["day_deterministic"])
    print(f"Full day: {seconds:.3f}s / 22200 ticks (fish/monsters excluded)")
    print("Two-process inventory:", summary["inventory_handoff"])
    print("Evidence:", out)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
