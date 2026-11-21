"""Run from the repository root: python docs/proof/phase-2/member-2/verify.py."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent


def main():
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join((str(ROOT / "tests"), str(ROOT))))
    log = []

    def run(*args, expected=(0,)):
        result = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=env,
                                capture_output=True, text=True, encoding="utf-8")
        log.append("$ python " + " ".join(map(str, args)) + "\n" + result.stdout + result.stderr
                   + f"\nExit code: {result.returncode}\n")
        (OUTPUT / "checks.txt").write_text("\n".join(log), encoding="utf-8")
        assert result.returncode in expected, log[-1]
        return result

    with tempfile.TemporaryDirectory(prefix="chonoi-tv2-v11-") as tmp:
        if os.name == "nt":
            shutil.copy2(sys.executable, Path(tmp) / "python3.exe")
            env["PYTHONHOME"] = sys.base_prefix
            env["PATH"] = tmp + os.pathsep + env.get("PATH", "")
        suite = run("-m", "unittest", "discover", "-s", "tests", "-v")
        for mode in ("gather", "quan"):
            run("-m", "chonoi.headless", "--mode", mode, "--seed", 1, "--ticks", 600,
                "--out", OUTPUT / (mode + ".jsonl"))
        run("-m", "chonoi.headless", "--mode", "gather", "--seed", 1, "--ticks", 600,
            "--out", Path(tmp) / "repeat.jsonl")
        assert (OUTPUT / "gather.jsonl").read_bytes() == (Path(tmp) / "repeat.jsonl").read_bytes()
        team = run("tools/check_team.py", expected=(0, 1))
    summary = {
        "tests_run": int(re.search(r"Ran (\d+) tests", suite.stderr).group(1)),
        "deterministic_gather_bytes": True,
        "team_check": {"exit_code": team.returncode, "output": (team.stdout + team.stderr).strip()},
        "runs": {},
    }
    for mode in ("gather", "quan"):
        path = OUTPUT / (mode + ".jsonl")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        summary["runs"][mode] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "end": rows[-1]}
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    print("PASS: suite, headless gather/quan, deterministic gather. TEAM exit:", team.returncode)


if __name__ == "__main__":
    main()
