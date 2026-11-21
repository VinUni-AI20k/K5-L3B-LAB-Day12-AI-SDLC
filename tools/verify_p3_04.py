"""Save real regression/CLI proof and explicitly labelled P3-03 mock proof.

python3 tools/verify_p3_04.py
Does not claim the current v1.1 CLI supports itemized v1.2 inventory.
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
    report = {"status": "PARTIAL: P3-04 kitchen ready; P3-02/P3-03 migration not integrated", "runs": []}
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

    # Not a CLI or a production stock-decay test: run the labelled boundary fixture.
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
        return {"fixture_type": "MOCK P3-03 boundary + real Session/Kitchen", "events": rows,
                "end": s.end_row(), "stock": s.sim.stock}
    a, b = boundary_trace(), boundary_trace()
    encoded = json.dumps(a, ensure_ascii=False, sort_keys=True)
    assert encoded == json.dumps(b, ensure_ascii=False, sort_keys=True)
    assert (a["end"]["money"], a["end"]["score"]) == (70, 370)
    report["mock_boundary"] = {"deterministic": True, "sha256": hashlib.sha256(encoded.encode()).hexdigest(), **a}
    sc = PROOF / "P3-04-itemized-probe.json"
    sc.write_text(json.dumps({"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}}) + "\n", encoding="utf-8")
    run("P3-04-itemized-cli-dependency", ["-m", "chonoi.headless", "--mode", "quan", "--seed", "42",
        "--ticks", "0", "--scenario", str(sc), "--out", str(PROOF / "P3-04-itemized-probe.jsonl")], expected=2)
    report["itemized_cli"] = "NOT INTEGRATED: v1.1 manifest/validator reject item arrays; exit 2 is a dependency, not v1.2 PASS"
    (PROOF / "P3-04-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Legacy CLI quan/day PASS; mock P3-03 pricing=59, tip=11, payout=70, score=370. Overall PARTIAL.")


if __name__ == "__main__":
    main()
