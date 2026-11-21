"""Verify P2-04 on this branch and optionally against an existing P2-03 ref.

python3 tools/verify_p2_04.py --integration-ref origin/lehuyanh
The optional integration runs in a temporary export; it never changes branches.
"""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs/proof/phase-2"
REPORT = {"runs": []}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def environment(root):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = os.pathsep.join((str(root / "tests"), str(root)))
    return env


def run(label, command, root=ROOT, expected=0):
    started = time.perf_counter()
    result = subprocess.run([str(p) for p in command], cwd=root, env=environment(root),
                            capture_output=True, encoding="utf-8")
    entry = {"label": label, "command": [str(p) for p in command], "exit_code": result.returncode,
             "seconds": round(time.perf_counter() - started, 4), "stdout": result.stdout, "stderr": result.stderr}
    REPORT["runs"].append(entry)
    if expected is not None and result.returncode != expected:
        raise AssertionError(f"{label}: exit {result.returncode}; {result.stderr[-2000:]}")
    return result


def suite(root, label):
    result = run(label, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root, expected=None)
    log = result.stdout + result.stderr
    (PROOF / f"{label}.txt").write_text(log, encoding="utf-8")
    print(label + ": " + " / ".join(log.splitlines()[-4:]), flush=True)
    if result.returncode:
        raise AssertionError(f"{label} failed; see docs/proof/phase-2/{label}.txt")
    # Keep the detailed unittest output in its log, not duplicated in the JSON.
    REPORT["runs"][-1].update(stdout="", stderr="", log=f"docs/proof/phase-2/{label}.txt")


def cli(root, label, mode, ticks, *extra, expected=0):
    contract = json.loads((root / "game.contract.json").read_text(encoding="utf-8"))
    out = PROOF / f"P2-04-{label}.jsonl"
    result = run(label, [*shlex.split(contract["headless_cmd"]), "--mode", mode, "--seed", "42",
                         "--ticks", str(ticks), "--out", out, *extra], root, expected)
    if result.returncode == 0:
        raw = out.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        REPORT["runs"][-1].update(output=str(out.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest(),
                                    event_counts=dict(Counter(r["name"] for r in rows if r["type"] == "event")),
                                    end=rows[-1])
        return rows
    return []


def check_playthrough(rows):
    ev = [r for r in rows if r["type"] == "event"]
    by_name = {name: [r for r in ev if r["name"] == name]
               for name in ("cook_started", "dish_ready", "dish_picked", "served", "paid")}
    assert all(len(items) == 4 for items in by_name.values())
    assert not any(r["name"] == "customer_left" for r in ev)
    assert [r["data"]["table_id"] for r in by_name["served"]] == ["T1", "T2", "T3", "T4"]
    assert sum(r["data"]["amount"] for r in by_name["paid"]) == 480
    snapshots = [r for r in rows if r["type"] == "snapshot" and r["phase"] == "quan"]
    assert max(sum(b["state"] == "cooking" for b in s["stoves"]) for s in snapshots) == 2
    for s in snapshots:
        assert [b["id"] for b in s["stoves"]] == ["B1", "B2"]
        assert [t["id"] for t in s["tables"]] == ["T1", "T2", "T3", "T4"]
        assert all(count >= 0 for count in s["stock"].values())
        assigned = sorted(c["id"] for c in s["customers"] if c["order_status"] == "assigned")
        dishes = [b["dish"] for b in s["stoves"] if b["dish"] is not None]
        if s["hand"] is not None:
            dishes.append(s["hand"])
        assert sorted(d["order_id"] for d in dishes) == assigned
    return ev


def isolated_day(ref, service, controls):
    """Use the actual colleague's DayLoop unchanged, with this restaurant overlay."""
    commit = subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()
    archive = subprocess.check_output(["git", "archive", commit], cwd=ROOT)
    REPORT["integration_ref"] = {"ref": ref, "commit": commit}
    with tempfile.TemporaryDirectory(prefix="chonoi-p2-04-") as temp:
        target = Path(temp).resolve()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(target, filter="data")
        overlay = ["chonoi/sim/quan.py", "chonoi/sim/kitchen.py", "chonoi/inventory.py",
                   "tests/test_restaurant_expansion.py", "tests/test_quan_integration.py",
                   "tests/fixtures/p2_04_quan.json", "tests/fixtures/p2_04_inputs.json"]
        for path in overlay:
            (target / path).parent.mkdir(parents=True, exist_ok=True)
            (target / path).write_bytes((ROOT / path).read_bytes())
        # Preserve the colleague's Gather/Day/Shop manifest and source. Overlay
        # only the Quán/menu data owned by P2-04, matching the future merge.
        contract = json.loads((target / "game.contract.json").read_text(encoding="utf-8"))
        ours = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
        for key in ("quan", "menu"):
            contract["tuning"][key] = ours["tuning"][key]
        contract["contract_version"] = "1.1"
        write_json(target / "game.contract.json", contract)
        REPORT["integration_ref"]["overlay"] = overlay + ["game.contract.json: quan/menu/version only"]
        suite(target, "P2-04-integrated-tests")
        default = cli(target, "day-default", "day", 22200, "--days", "1")
        assert default[-1]["reason"] == "days_complete" and default[-1]["days_completed"] == 1
        assert default[-1]["ticks"] == 22200

        hold = [kind for kind, count in service["quan"]["stock"].items() for _ in range(count)]
        quan = {k: deepcopy(v) for k, v in service["quan"].items() if k != "stock"}
        planned = {c["dish_id"]: 1 for c in quan["customers"]}
        fixture = {"day": {"money": 200, "earned": 450,
                           "day_plan": [{"day": day, "dishes": planned} for day in (1, 2)]},
                   "gather": {"hold": hold, "random_fish": False, "monsters": []}, "quan": quan}
        sc = write_json(PROOF / "P2-04-day-scenario.json", fixture)
        shifted = [{**fr, "tick": fr["tick"] + 2} for fr in controls["frames"]]
        buy_tick = 1 + round(contract["tuning"]["quan"]["duration_s"] * contract["tuning"]["tick_hz"])
        frames = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, *shifted,
                  {"tick": buy_tick, "buy": "oxygen", "shop_done": True}]
        inp = write_json(PROOF / "P2-04-day-inputs.json", {"frames": frames})
        first = cli(target, "day-service-a", "day", 22200, "--days", "1", "--scenario", sc,
                    "--inputs", inp, "--snapshot-every", "1")
        second = cli(target, "day-service-b", "day", 22200, "--days", "1", "--scenario", sc,
                     "--inputs", inp, "--snapshot-every", "1")
        assert (PROOF / "P2-04-day-service-a.jsonl").read_bytes() == (PROOF / "P2-04-day-service-b.jsonl").read_bytes()
        check_playthrough(first)
        end = first[-1]
        assert (end["money"], end["earned"], end["reputation"], end["score"]) == (480, 930, 3.8, 1230)
        assert end["reason"] == "days_complete" and end["days_completed"] == 1
        assert all("day" in r for r in first if r["type"] in ("snapshot", "event"))
        for before, after in zip(first, first[1:]):
            if before.get("name") == "quan_end":
                assert before["phase"] == "quan" and after["name"] == "phase_start" and after["phase"] == "shop"
        next_day = buy_tick + 1
        # Release Shop's latch when entering Day 2, then reuse the exact controls.
        frames.extend([{"tick": next_day, "shop_done": False, "interact": True},
                       {"tick": next_day + 1, "interact": False}])
        frames.extend({**fr, "tick": fr["tick"] + next_day + 2} for fr in controls["frames"])
        frames.append({"tick": next_day + buy_tick, "buy": "hp", "shop_done": True})
        inp2 = write_json(PROOF / "P2-04-two-days-inputs.json", {"frames": frames})
        days = cli(target, "two-days-service", "day", 44400, "--days", "2", "--scenario", sc,
                   "--inputs", inp2, "--snapshot-every", "100")
        end = days[-1]
        assert (end["money"], end["earned"], end["reputation"], end["score"]) == (710, 1410, 4.6, 1810)
        assert end["days_completed"] == 2 and end["reason"] == "days_complete"
        starts = [r for r in days if r["type"] == "snapshot" and r.get("day") == 2 and r["phase_tick"] == 0]
        assert starts[0]["active_upgrades"] == {"oxygen": 1}
        assert starts[0]["player"]["oxygen_max_ticks"] == 2700
        REPORT["day_integration"] = {"status": "PASS in isolated export; not merged into working branch",
                                     "one_day_deterministic_bytes": True, "one_day_end": first[-1],
                                     "two_days_end": end}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration-ref")
    args = parser.parse_args()
    PROOF.mkdir(parents=True, exist_ok=True)
    REPORT.update(base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
                  python=sys.version, current_branch_day="P2-03 integrated; checked by current-day-probe")
    paths = ["game.contract.json", "chonoi/sim/quan.py", "chonoi/sim/kitchen.py", "chonoi/inventory.py",
             "chonoi/scenario.py", "tests/test_restaurant_expansion.py", "tests/test_quan_integration.py",
             "tests/fixtures/p2_04_quan.json", "tests/fixtures/p2_04_inputs.json", "tools/verify_p2_04.py"]
    REPORT["source_sha256"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    suite(ROOT, "P2-04-tests")
    cli(ROOT, "default", "quan", 10800)
    service = json.loads((ROOT / "tests/fixtures/p2_04_quan.json").read_text(encoding="utf-8"))
    controls = json.loads((ROOT / "tests/fixtures/p2_04_inputs.json").read_text(encoding="utf-8"))
    runs = [cli(ROOT, label, "quan", 10800, "--scenario", ROOT / "tests/fixtures/p2_04_quan.json",
                "--inputs", ROOT / "tests/fixtures/p2_04_inputs.json", "--snapshot-every", "1")
            for label in ("service-a", "service-b")]
    assert (PROOF / "P2-04-service-a.jsonl").read_bytes() == (PROOF / "P2-04-service-b.jsonl").read_bytes()
    ev = check_playthrough(runs[0])
    assert (runs[0][-1]["money"], runs[0][-1]["earned"], runs[0][-1]["reputation"], runs[0][-1]["score"]) == (480, 480, 3.8, 780)
    REPORT["standalone"] = {"status": "PASS", "deterministic_bytes": True, "events": ev, "end": runs[0][-1]}
    kinds = ["ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_keo", "keo_neo"]
    sc = write_json(PROOF / "P2-04-dock-scenario.json", {"gather": {"hold": kinds, "random_fish": False}})
    inp = write_json(PROOF / "P2-04-dock-inputs.json", {"frames": [{"tick": 0, "interact": True}]})
    for label in ("a", "b"):
        cli(ROOT, "gather-" + label, "gather", 1, "--scenario", sc, "--inputs", inp,
            "--inventory-out", PROOF / f"P2-04-inventory-{label}.json")
    assert (PROOF / "P2-04-inventory-a.json").read_bytes() == (PROOF / "P2-04-inventory-b.json").read_bytes()
    stock = cli(ROOT, "inventory-quan", "quan", 0, "--inventory", PROOF / "P2-04-inventory-a.json")[0]["stock"]
    assert stock == {k: 1 for k in kinds}
    REPORT["inventory"] = {"deterministic_bytes": True, "stock": stock}
    day = cli(ROOT, "current-day-probe", "day", 22200, "--days", "1")
    assert day[-1]["reason"] == "days_complete" and day[-1]["days_completed"] == 1
    if args.integration_ref:
        isolated_day(args.integration_ref, service, controls)
    REPORT["overall"] = "PASS restaurant/day checks; full Phase 2 DoD not assessed"
    print("P2-04: restaurant PASS; 4 dishes paid, money=480, reputation=3.8, score=780.", flush=True)
    print("Day integration: " + REPORT.get("day_integration", {}).get("status", "not requested"), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT["verification_error"] = str(exc)
        raise
    finally:
        PROOF.mkdir(parents=True, exist_ok=True)
        write_json(PROOF / "P2-04-results.json", REPORT)
