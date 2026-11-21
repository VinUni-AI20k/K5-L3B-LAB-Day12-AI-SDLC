"""Save regression/CLI proof and traces using the integrated P3-03 engine.

python3 tools/verify_p3_04.py
Requires the merged v1.2 itemized inventory and P3-03 stock implementation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs/proof/phase-3"


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "tests"), str(ROOT)))
    report = {"status": "P3-02/P3-03 integrated; full Phase 3 DoD not assessed", "runs": []}
    report["base_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report["python"] = sys.version
    report["source_sha256"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "chonoi/sim/freshness_pricing.py", "chonoi/sim/kitchen.py", "tests/test_freshness_pricing.py",
        "tests/p3_04_boundary_fixture.py", "tests/fixtures/p3_04_freshness.json", "game.contract.json")}

    def run(label, args, expected=0):
        command = [sys.executable, *args]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding="utf-8")
        (PROOF / (label + ".txt")).write_text(result.stdout + result.stderr, encoding="utf-8")
        report["runs"].append({"label": label, "command": command, "exit_code": result.returncode,
                               "log": label + ".txt"})
        assert result.returncode == expected, (label, result.stderr[-2000:])
        return result

    result = run("P3-04-tests", ["-m", "unittest", "discover", "-s", "tests", "-v"])
    print("\n".join((result.stdout + result.stderr).splitlines()[-4:]), flush=True)
    for mode, ticks, extra in (
        ("quan", "10800", ["--scenario", "tests/fixtures/p2_04_quan.json", "--inputs", "tests/fixtures/p2_04_inputs.json"]),
        ("day", "22200", ["--days", "1"]),
    ):
        label = "P3-04-legacy-" + mode
        out = PROOF / (label + ".jsonl")
        run(label, ["-m", "chonoi.headless", "--mode", mode, "--seed", "42", "--ticks", ticks,
                    "--out", str(out), *extra])
        end = json.loads(out.read_text(encoding="utf-8").splitlines()[-1])
        report["runs"][-1]["end"] = end
        if mode == "quan":
            assert (end["money"], end["reputation"], end["score"]) == (480, 3.8, 780)
        else:
            assert end["days_completed"] == 1 and end["reason"] == "days_complete"

    # Trace a Session with native stock processing; CLI checks are separate.
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT))
    from p3_04_boundary_fixture import session, step
    def boundary_trace():
        s = session()
        rows = step(s, True)
        for _ in range(359):
            rows.extend(step(s))
        rows.extend(step(s, True))
        s.sim.pos = [9, 2]
        rows.extend(step(s, True))
        for _ in range(600):
            rows.extend(step(s))
        return {"fixture_type": "Real P3-03 stock engine + Session/Kitchen", "events": rows,
                "end": s.end_row(), "stock": s.sim.stock}
    a, b = boundary_trace(), boundary_trace()
    encoded = json.dumps(a, ensure_ascii=False, sort_keys=True)
    assert encoded == json.dumps(b, ensure_ascii=False, sort_keys=True)
    assert (a["end"]["money"], a["end"]["score"]) == (70, 370)
    report["integration_boundary"] = {"deterministic": True, "sha256": hashlib.sha256(encoded.encode()).hexdigest(), **a}
    sc = PROOF / "P3-04-itemized-probe.json"
    sc.write_text(json.dumps({"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}}) + "\n", encoding="utf-8")
    run("P3-04-itemized-cli", ["-m", "chonoi.headless", "--mode", "quan", "--seed", "42",
        "--ticks", "0", "--scenario", str(sc), "--out", str(PROOF / "P3-04-itemized-probe.jsonl")])
    report["itemized_cli"] = "Itemized stock accepted by integrated v1.2 CLI"
    (PROOF / "P3-04-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CLI quan/day PASS; real P3-03 pricing=59, tip=11, payout=70, score=370.")


if __name__ == "__main__":
    main()
