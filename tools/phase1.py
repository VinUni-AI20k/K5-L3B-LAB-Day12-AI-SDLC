"""Lệnh kiểm nhanh Phase 1 dùng chung trên Windows và macOS/Linux."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SMOKE = "tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "smoke"))
    args = parser.parse_args()
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(("tests", ".")), "PYTHONUTF8": "1"}

    if args.command == "smoke":
        return subprocess.call([sys.executable, "-m", "unittest", SMOKE, "-v"], cwd=ROOT, env=env)

    team_check = subprocess.call([sys.executable, "tools/check_team.py"], cwd=ROOT)
    suite = subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, env=env)
    return suite or team_check


if __name__ == "__main__":
    sys.exit(main())
