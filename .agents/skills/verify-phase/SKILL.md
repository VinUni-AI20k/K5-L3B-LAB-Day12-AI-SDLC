---
name: verify-phase
description: Run team validation, unit tests, two-process gather-to-quan smoke test, and byte-for-byte headless determinism verification before committing or opening a PR.
---

# Skill: `verify-phase`

Use this skill before committing code, opening a Pull Request, or tagging a phase release (`phase-1` .. `phase-4`).

## Step 1: Validate `TEAM.md` and `game.contract.json`
Run the team checker to ensure `TEAM.md` handles and `team_size` in `game.contract.json` are valid:
```bash
python3 tools/check_team.py
```

## Step 2: Run the Full Unit & Live Server Test Suite
All unit tests, scenario validation tests, smoke tests, and live HTTP server tests must pass:
```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

## Step 3: Verify Headless Byte-for-Byte Determinism
Verify that two runs with the same seed and parameters produce identical JSONL outputs byte-for-byte for both `gather` and `quan`:
```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 120 --out /tmp/g1.jsonl --inventory-out /tmp/inv1.json && \
python3 -m chonoi.headless --mode gather --seed 42 --ticks 120 --out /tmp/g2.jsonl --inventory-out /tmp/inv2.json && \
cmp -s /tmp/g1.jsonl /tmp/g2.jsonl && \
python3 -m chonoi.headless --mode quan --seed 42 --ticks 120 --out /tmp/q1.jsonl && \
python3 -m chonoi.headless --mode quan --seed 42 --ticks 120 --out /tmp/q2.jsonl && \
cmp -s /tmp/q1.jsonl /tmp/q2.jsonl && \
rm -f /tmp/g1.jsonl /tmp/g2.jsonl /tmp/inv1.json /tmp/inv2.json /tmp/q1.jsonl /tmp/q2.jsonl
```

## Step 4: Record Evidence
- If any check fails, fix the implementation (do not weaken contract tests).
- Log your AI tool usage in `docs/ai-usage-log.md` and save verification outputs in `docs/proof/phase-1/`.
