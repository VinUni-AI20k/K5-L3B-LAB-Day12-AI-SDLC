# Soak check — Phase 4

- Code commit: `80c8ff4` (`main`, after PR #15); QA run on `7d9b946`.
- Command: `python3 -m chonoi.soak --seed 7 --days 10 --out docs\proof\phase-4\soak.json`
- Result: `days=10`, `days_completed=10`, `crashes=0`; `duration_s=3.603419`.
- Determinism: repeated the same command with a temporary output file; `days`, `days_completed`, `crashes`, and `results` matched exactly. Only `duration_s` was excluded from comparison as required. The temporary file was removed.

Raw output: [soak.json](./soak.json).
