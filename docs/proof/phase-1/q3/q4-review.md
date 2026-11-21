# Q4 code review — Quoosc / Q3 handoff

**Ngày:** 2026-11-21 (Asia/Bangkok)
**Target tree:** `cfaa8bfcb7978c998ed449628eb18da901ec352f` (`Quoosc`, clean at review start)
**Q4 source history reviewed:** `dcf6694a56a8149ac1158973670a51e82371edca` (cook/pick/serve) and `5d777333800394b942d97252a28cb4685e4bc696` (payment/tip/reputation), both present in target tree.
**Status:** Findings recorded; not an approval. No new Q4 diff was present in the working tree at review start.

## Scope and evidence

Read `QuanSim._tick_customers`, `_tick_stoves`, `_nearest_interaction`, `_interact`, `_has_reserved_recipe`, the current Q4-facing tests in `tests/test_p1_logic.py`, and the historical Q4 commits above. The current tests cover a happy path through cook/serve/pay and a waiting departure; they do not cover departure after cook-start.

I ran a direct `QuanSim` scenario from the repository tuning: one `C1` at `T1`, `goi_bong_sung`, reservation equal to its recipe, stock equal to that recipe, and `patience_ticks_left=2`. At the stove, one interact step emitted `cook_started`; the next step emitted `customer_left`; after the cook timer, the stove became `ready`, and a further interact emitted `dish_picked` although `customers=[]`. The hand then contained `goi_bong_sung` with no customer/order identity to serve or clean up. This is reproducible with the current code and does not require a fake Q4 seam.

## Finding

### Q4-F1 — A dish can become orphaned after its customer leaves during cooking

`_interact` stores only `dish_id` on the stove/hand; cook-start changes the customer to `ordered`, while `_tick_customers` still decrements patience in both `waiting` and `ordered` states and removes an expired customer. `_tick_stoves` then completes cooking without checking whether the associated customer/order still exists. The dish can be picked up, but `_interact` can only serve it to a customer at the targeted table whose `dish_id` matches. With the original customer removed, the cooked dish has no lifecycle owner and can remain stranded in `hand` (stock has already been consumed).

**Impact:** stale food can occupy the hand or stove, no serve/payment can complete for that order, and any future end-condition query that does not account for orphaned dishes may misreport active work. This also means the Q3 departure notification and Q4 dish cleanup boundary is not yet coherent.

**Reproduction outcome:** `tick1 cook_started; tick2 customer_left; post-cook customers=[] / stove=ready; pickup dish_picked / hand=goi_bong_sung`.

**Suggested owner/action:** Q4 should preserve customer/order association through stove and hand, then define the cooked-dish cleanup/serve policy when that customer departs. Confirm whether ordered customers are still allowed to time out during cooking from the authoritative PRD before changing that policy. Keep the single left-penalty owner explicit.

## Checklist status

- Cook-start consumes recipe stock and clears that customer's reservation in one ordinary happy-path interaction; repeated cooking interaction cannot start a second cook while the stove is cooking. The broader lifecycle is **not coherent** for the departure case above.
- Customer/order/dish/stove/hand association: **finding Q4-F1**; stove/hand contain dish identity only.
- Serve/eating/payment: happy path covered by existing test; repeated `paid` is prevented by removal after payment. Official same-tick semantics remain unverified.
- Penalty ownership and event schema: implementation currently applies left reputation delta inside `_tick_customers`; no official contract was available in the reviewed sources, so one-owner approval remains open.
- Scenario validation for assigned/eating and exact no-dish/end semantics: not reviewed as Q4 acceptance criteria; PRD/Test Contract source gap remains open.

No `quan.py` or test files were changed as part of this review.

