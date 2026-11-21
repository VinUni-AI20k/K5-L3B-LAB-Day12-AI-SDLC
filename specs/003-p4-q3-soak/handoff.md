# Handoff — AC-P4-03

Implementation: `chonoi/soak.py`; tests: `tests/test_p4_soak.py`; real output/replay: [`docs/proof/phase-4/soak-run.txt`](../../docs/proof/phase-4/soak-run.txt) and `soak.json` / `soak-replay.json`.

QA/Integrator should verify both run files, their matching gameplay fields and `exit 0`. The fast-dock bot intentionally leaves QuanSim uncontrolled and does not gather, so `earned=0` in the observed run. This proves lifecycle/stability across ten days, not economy balance or player strategy quality. Benchmark, UI warnings, packaging and release remain outside Quoosc's assigned soak task.
