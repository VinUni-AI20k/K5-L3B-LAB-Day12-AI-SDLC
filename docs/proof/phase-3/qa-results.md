# Phase 3 QA evidence

These are branch-level QA results on `v1.2`, not final release evidence for `main`.

## Focused acceptance checks

| Check | Test | Observed result |
|---|---|---|
| Freshness boundary | `test_gather_threshold_spoils_once_at_tick_one` | `I1` at fresh 30 emits one `spoiled` event at tick 1 and is below 30 afterward. |
| Reservation retry | `test_spoiled_reserved_item_releases_and_reholds_order_once` | Spoiled `I1` is released; `C1` holds `I2`; no repeated spoil event on tick 2. |
| Freshness price | `test_cook_price_floors_after_freshness_adjustment` | A 60-price dish using fresh `49.9958…` starts at base price 29 (floor). |
| File handoff | `test_inv_01_gather_writes_inventory_quan_reads_it` | IDs/kinds survive gather output, the inventory file, and a tick-0 `--inventory` read; freshness agrees within 0.01. Artifacts: [gather JSONL](integration.gather.jsonl), [inventory file](integration.inventory.json), [quan JSONL](integration.quan.jsonl). |
| Day handoff | `test_day_handoff_preserves_gather_freshness_in_same_tick` | At tick 1 the day session is in `quan`; stock retains `I1` at gather's post-decay freshness without an extra decay. Artifact: [day JSONL](day.jsonl). |

## Regression status

The Khoa-owned targeted command passed **36/36**:

```powershell
$env:PYTHONPATH='tests;.'
python3 -m unittest test_smoke_p1 test_python_starter_units test_qa_phase2 test_qa_phase3 -v
```

Raw output: [regression.txt](regression.txt).

The complete suite is **blocked**: 112 tests ran, with 12 failures and 5 errors. The selected failure/error names are captured in [full-regression.txt](full-regression.txt). The remaining cases are stale v1.1 fixtures/assertions in:

- Hiếu: `test_gather_lat1.py` (1 failure), `test_gather_lat2.py` (4 failures).
- Chuẩn: `test_gather_monsters.py` (2 failures), `test_quan_lat3.py` (3 errors).
- Quân: `test_quan_lat4.py` (3 failures), `test_p2_quan_shop.py` (2 failures, 2 errors).

Do not treat this as an all-green Phase 3 integration. Re-run the full suite and the HUD check after those migrations land; merge/tag on `main` remains gated by the ADR integration criteria.
