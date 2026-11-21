"""Tái tạo bằng chứng Gather Core: python docs/proof/phase-1/member-2/verify.py."""

import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
PROOF = Path(__file__).resolve().parent
OUTPUT = PROOF / "prd-correction"
sys.path.insert(0, str(ROOT))

from chonoi.contract import load_contract
from chonoi.inventory import read_inventory
from chonoi.scenario import load_scenario


def main():
    OUTPUT.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join((str(ROOT / "tests"), str(ROOT))))
    log = []

    def run(*args, expected=(0,)):
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8")
        log.append("$ python " + " ".join(map(str, args)) + "\n" + result.stdout
                   + f"Exit code: {result.returncode}\n")
        (OUTPUT / "checks.txt").write_text("\n".join(log), encoding="utf-8")
        assert result.returncode in expected, log[-1]
        return result

    def headless(name, ticks, scenario=None, inputs=None, inventory=None, every=10, out=None):
        args = ["-m", "chonoi.headless", "--mode", "gather", "--seed", "1",
                "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", str(out or OUTPUT / (name + ".jsonl"))]
        for flag, value in (("--scenario", scenario), ("--inputs", inputs), ("--inventory-out", inventory)):
            if value:
                args.extend((flag, str((OUTPUT if flag == "--inventory-out" else PROOF) / value)))
        run(*args)

    # Launcher cục bộ cho headless_cmd=python3 trên Windows, không sửa contract.
    with tempfile.TemporaryDirectory(prefix="chonoi-tv2-") as tmp:
        if os.name == "nt":
            shutil.copy2(sys.executable, Path(tmp) / "python3.exe")
            env["PYTHONHOME"] = sys.base_prefix
            env["PATH"] = tmp + os.pathsep + env.get("PATH", "")
        tuning = load_contract()["tuning"]
        for path in PROOF.glob("*.scenario.json"):
            load_scenario(path, "gather", tuning)
        suite = run("-m", "unittest", "discover", "-s", "tests", "-v")
        run("-m", "unittest", "tests.test_python_starter_units", "-v")
        headless("gather_run", 600)
        run("-m", "chonoi.headless", "--mode", "quan", "--seed", "1", "--ticks", "600",
            "--out", str(OUTPUT / "quan_run.jsonl"))
        headless("oxygen-cycle", 32, "oxygen-cycle.scenario.json", "oxygen-cycle.inputs.json", every=1)
        headless("faint", 220, "faint.scenario.json", inventory="faint.inventory.json")
        headless("dock", 1, "dock.scenario.json", "dock.inputs.json", "dock.inventory.json")
        headless("faint", 220, "faint.scenario.json", out=Path(tmp) / "repeat.jsonl")
        assert (OUTPUT / "faint.jsonl").read_bytes() == (Path(tmp) / "repeat.jsonl").read_bytes()
        assert read_inventory(OUTPUT / "faint.inventory.json") == {}
        assert read_inventory(OUTPUT / "dock.inventory.json") == {"ca_loc": 1, "bong_sung": 2}
        team = run("tools/check_team.py", expected=(0, 1))

    summary = {"deterministic_faint_bytes": True, "faint_inventory_empty": True,
               "tests_run": int(re.search(r"Ran (\d+) tests", suite.stdout).group(1)),
               "team_check": {"exit_code": team.returncode, "output": team.stdout.strip()}, "runs": {}}
    for name in ("gather_run", "quan_run", "oxygen-cycle", "faint", "dock"):
        path = OUTPUT / (name + ".jsonl")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        summary["runs"][name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "end": rows[-1],
                                  "events": [{"tick": r["tick"], "name": r["name"], "data": r["data"]}
                                             for r in rows if r["type"] == "event"]}
    assert [e["name"] for e in summary["runs"]["oxygen-cycle"]["events"]] == ["dive", "oxygen_empty", "surface"]
    faint_events = summary["runs"]["faint"]["events"]
    assert [(e["tick"], e["name"]) for e in faint_events] == [
        (1, "oxygen_empty"), (60, "choke"), (120, "choke"), (180, "choke"), (180, "faint"), (180, "gather_end")]
    for name in ("oxygen-cycle", "faint"):
        empty = [e for e in summary["runs"][name]["events"] if e["name"] == "oxygen_empty"]
        assert len(empty) == 1 and empty[0]["data"] == {"oxygen_ticks": 0}
    assert faint_events[-2]["data"] == {"cause": "choke", "lost": ["bong_sung", "ca_loc"], "hp": 0}
    assert faint_events[-1]["data"] == {"reason": "fainted", "inventory": {"items": {}}}
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: unit/smoke, fixtures, oxygen cycle, faint, inventory, deterministic bytes.")
    print("TEAM:", team.stdout.strip())


if __name__ == "__main__":
    main()
