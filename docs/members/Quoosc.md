# Quoosc — Q3 contribution (draft by Codex)

This working diff adds Q3 customer hydration, atomic reservation/consume/release, elapsed-tick arrivals, `random_customers` handling, and waiting-customer expiry. It includes outcome tests and standalone fixtures; run details and remaining source gaps are in [Q3 proof](../proof/phase-1/q3/README.md). The full PRD-0/Test Contract was not present in the local sources, so source-sensitive rules remain provisional.

The Q4 review at the starting tree recorded a reproducible orphaned-dish case when a customer leaves during cooking. It is a finding for the Q4 owner, not an approval. The baseline test command initially failed because this Windows environment lacks `python3`; a temporary interpreter shim fixed command resolution. This caught an environment issue before interpreting the result as a code failure.

Quốc should review and confirm this draft before using it as a personal reflection.
