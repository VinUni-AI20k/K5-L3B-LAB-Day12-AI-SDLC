"""Tái tạo bằng chứng Gather Core: python docs/proof/phase-1/member-2/verify.py."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
PROOF = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from chonoi.contract import load_contract
from chonoi.inventory import read_inventory
from chonoi.scenario import load_scenario


def main():
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join((str(ROOT / "tests"), str(ROOT))))
    log = []

    def run(*args, expected=0):
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8")
        log.append("$ python " + " ".join(map(str, args)) + "\n" + result.stdout
                   + f"Exit code: {result.returncode}\n")
        (PROOF / "commit-6-checks.txt").write_text("\n".join(log), encoding="utf-8")
        assert result.returncode == expected, log[-1]

    def headless(name, ticks, scenario=None, inputs=None, inventory=None, every=10, out=None):
        args = ["-m", "chonoi.headless", "--mode", "gather", "--seed", "1",
                "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", str(out or PROOF / (name + ".jsonl"))]
        for flag, value in (("--scenario", scenario), ("--inputs", inputs), ("--inventory-out", inventory)):
            if value:
                args.extend((flag, str(PROOF / value)))
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
        run("-m", "unittest", "discover", "-s", "tests", "-v")
        run("-m", "unittest", "tests.test_python_starter_units", "-v")
        headless("gather_run", 600)
        run("-m", "chonoi.headless", "--mode", "quan", "--seed", "1", "--ticks", "600",
            "--out", str(PROOF / "quan_run.jsonl"))
        headless("oxygen-cycle", 32, "oxygen-cycle.scenario.json", "oxygen-cycle.inputs.json", every=1)
        headless("faint", 220, "faint.scenario.json", inventory="faint.inventory.json")
        headless("dock", 1, "dock.scenario.json", "dock.inputs.json", "dock.inventory.json")
        headless("faint", 220, "faint.scenario.json", out=Path(tmp) / "repeat.jsonl")
        assert (PROOF / "faint.jsonl").read_bytes() == (Path(tmp) / "repeat.jsonl").read_bytes()
        assert read_inventory(PROOF / "faint.inventory.json") == {}
        assert read_inventory(PROOF / "dock.inventory.json") == {"ca_loc": 1, "bong_sung": 2}
        run("tools/check_team.py", expected=1)  # TV3–6 còn placeholder tại thời điểm bàn giao.

    summary = {"deterministic_faint_bytes": True, "faint_inventory_empty": True,
               "team_check": "chưa đạt: TV3–6 còn placeholder", "runs": {}}
    for name in ("gather_run", "quan_run", "oxygen-cycle", "faint", "dock"):
        path = PROOF / (name + ".jsonl")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        summary["runs"][name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "end": rows[-1],
                                  "events": [{"tick": r["tick"], "name": r["name"]}
                                             for r in rows if r["type"] == "event"]}
    assert [e["name"] for e in summary["runs"]["oxygen-cycle"]["events"]] == ["dive", "oxygen_empty", "surface"]
    faint_events = summary["runs"]["faint"]["events"]
    assert [(e["tick"], e["name"]) for e in faint_events] == [
        (1, "oxygen_empty"), (60, "choke"), (120, "choke"), (180, "choke"), (180, "faint"), (180, "gather_end")]
    (PROOF / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: unit/smoke, fixtures, oxygen cycle, faint, inventory, deterministic bytes.")
    print("TEAM: chưa đạt do thành viên 3–6 chưa điền GitHub handle.")


if __name__ == "__main__":
    main()
