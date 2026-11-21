# Quoosc — Q3 contribution (draft by Codex)

This working diff adds Q3 customer hydration, atomic reservation/consume/release, elapsed-tick arrivals, `random_customers` handling, and waiting-customer expiry. It includes outcome tests and standalone fixtures; run details and remaining source gaps are in [Q3 proof](../proof/phase-1/q3/README.md). The full PRD-0/Test Contract was not present in the local sources, so source-sensitive rules remain provisional.

The Q4 review at the starting tree recorded a reproducible orphaned-dish case when a customer leaves during cooking. It is a finding for the Q4 owner, not an approval. The baseline test command initially failed because this Windows environment lacks `python3`; a temporary interpreter shim fixed command resolution. This caught an environment issue before interpreting the result as a code failure.

Quốc should review and confirm this draft before using it as a personal reflection.

Phase 2 draft: added `menu_filter`, customer `order_tick` and tests for four tables and six fixture dishes; [evidence](../proof/phase-2/q3/README.md). Reviewed Q4 branch `8b3b93f`: its cooking flow needs reconciliation with the Q3 reservation ledger. DaySim and official v1.1 remain pending. Quốc should confirm the personal reflection and lessons before final submission.

Update: reviewed Q4 `5dbdf13`, which uses the reservation ledger; produced an isolated proposed patch for filter and order validation and checked the combined tests. This is a factual draft, awaiting Quốc's personal confirmation.
