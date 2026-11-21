# Q3 fixtures (Phase 1)

These JSON files contain only fields accepted by the current scenario loader.
They are local Q3 test inputs and are not PRD acceptance fixtures because the
Phase 1 customer schema/decisions D-01..D-09 have not been verified against the
official PRD/Test Contract yet.

| Fixture | Use |
|---|---|
| `spawn-one-dish.json` | One available recipe, random arrivals enabled, T1 initially empty. |
| `waiting-expiry.json` | One waiting customer with a two-tick patience boundary. |
| `invalid-overreserved.json` | A reservation exceeding physical stock; expected BadInput before JSONL output. |
| `invalid-partial-recipe.json` | A reservation missing part of a valid dish recipe; expected BadInput before JSONL output. |
| `reserved-before-cook.json` | Waiting customer whose raw recipe is reserved for Q4 cook-start. |
| `ordered-during-cook.json` | Local `ordered` customer linked to B1 while a dish cooks; reservation already consumed. |
| `eating-before-paid.json` | Eating customer with no raw reservation and a remaining eat timer for Q4 payment. |

The stock in scenario fixtures uses the `scenario.stock` shape. Do not combine
these inputs with `--inventory`. `random_customers` is a supported scenario
field. Tick semantics and reservation accounting asserted in `test_p1_q3.py`
are provisional where the feature spec says so. The `ordered`/`eating`
transitions and their dish/stove linkage in the three Q3/Q4 handoff fixtures
are `[PROPOSED]`: confirm their exact semantics and event ownership against the
official PRD/Test Contract before treating them as acceptance evidence.
