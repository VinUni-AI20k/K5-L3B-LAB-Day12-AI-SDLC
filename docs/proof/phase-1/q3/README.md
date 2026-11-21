# Q3 proof — Quoosc / Phase 1

Status is scoped to this working diff. `FR-Q3-*` and `TC-Q3-*` are internal IDs, not official lecturer ACs. The local workspace did not contain the Phase 1 PRD-0/Test Contract described in the feature sources; D-01..D-09 semantics remain provisional/open where noted. The existing Q4 happy path was run against real QuanSim code; no official full-lifecycle acceptance is claimed.

## Checkout and baseline

- Repo: `E:/VINAITHUCCHIEN/K5-L3B-DAY12-NhomF7-AI-SDLC`
- Branch: `Quoosc`; starting HEAD: `cfaa8bfcb7978c998ed449628eb18da901ec352f` (clean, same as `origin/main` and `origin/Quoosc`).
- Baseline suite: 44 tests, exit 0, 7.07 s, using installed Python 3.11. The contract subprocess command is `python3`; Windows had no `python3` application, so a temporary `python3.exe` copy of the installed interpreter was prepended to PATH outside the repo. The first native attempt without that shim failed because of command resolution (not a test assertion).
- Baseline headless: gather and quan, seed 1, 600 ticks; both exit 0. Captured files are `baseline-gather.jsonl` and `baseline-quan.jsonl`.
- Raw baseline unittest output: `baseline-tests.txt`.

The branch fast-forward to `b72b565` occurred during work and is preserved; the SHAs are recorded in the feature kit's `sources.md` and in `headless-proof.txt`. No task commit or push was created.

## Q3 decisions used in this diff

- **PROPOSED D-01:** supported customer states remain the local loader's `waiting`, `ordered`, `eating`; missing `reserved` is copied from the menu recipe for `waiting` customers. Local Q4 marks a customer `ordered` at cook-start, so `ordered`/`eating` fixture defaults have no raw reservation. Nested customer values are deep-copied.
- **PROPOSED D-02/D-03/D-04:** random arrivals default on; elapsed ticks drive first and interval scheduling; one free numeric-ID-sorted table and one recipe are selected at each due tick; no backlog on a missed/full/no-stock opportunity; Q3 draws use `Streams`.
- **PROPOSED D-05:** physical stock and unconsumed reservations are one ledger. Reserve is atomic; cook-start consumes/debits once; release frees availability without refunding stock. Private status is kept outside serialized customer data.
- **PROPOSED D-06/D-07:** keep the existing simulation step order and event envelope; patience applies to waiting/ordered only, and customer-left notification/reputation update occurs once in `_tick_customers`. This preserves the current single owner; Q4 must not apply the same penalty again unless the team changes ownership. Same-tick semantics and official event payload remain unverified.
- **OPEN D-08:** Q3 exposes `_can_accept_order()` and `_has_active_work()`; it no longer emits speculative `no_dish` events or ends the shift for that condition. Exact official no-dish rule remains open.
- **D-09:** scenario validation rejects non-boolean `random_customers`; runtime hydration requires a held reservation to match the full recipe and checks aggregate reservations against actual stock (including inventory-file stock) before the runner opens output.

## Verification results

- Q3-only: 23 tests, exit 0 (0.25 s); see `q3-tests.txt`.
- Full regression on the implementation tree: 68 tests, exit 0 (5.61 s); see `regression.txt`.
- Q4 happy-path handoff tests: 2 existing tests, exit 0; see `q4-happy-path-tests.txt`. This is real in-process QuanSim/Q4 code, not a fake seam; it does not resolve the Q4-F1 departure-during-cooking case.
- Q4 review: [`q4-review.md`](q4-review.md) records the target source and a reproducible orphaned-dish finding. It is not an approval.
- No `specify` CLI, `.specify/` project state, or packaged `python-fact-grounded-coding` / `phase-1-verification` skills were available locally. PRD lookup at the supplied Claude artifact URL was inaccessible; the source note in the feature kit describes the same phase-data/login gap.
- Each provisional test is evidence for the listed internal behavior only, not official AC acceptance.

## Reproduction inputs and changed files

- Tuning source: `game.contract.json`; unit tests make tuning copies only for multi-table and accelerated schedule cases.
- Fixture set: `tests/fixtures/p1/q3/` (one-dish spawn, waiting expiry, reserved-before-cook, ordered-during-cook, eating-before-paid, overreserved and partial-recipe invalid cases).
- Changed product code: `chonoi/sim/quan.py`, `chonoi/scenario.py`. Test code: `tests/test_p1_q3.py`. Contribution, verification and proof documents are listed by Git status; no contract-wide file or UI was changed.
- Test commands: `python3 -m unittest discover -s tests -p 'test_p1_q3.py' -v` and `python3 -m unittest discover -s tests -v`. This Windows checkout used the PATH shim described above; headless outputs and replay command are in `headless-proof.txt`.
