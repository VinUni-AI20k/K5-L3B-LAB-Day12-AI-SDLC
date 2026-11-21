"""TEST ONLY: scripted P3-03 boundary, not a production inventory engine.

Inject itemized stock after legacy construction. Before interaction, simulate
decay and optionally replace spoiled claims with IDs explicitly supplied by
the test. Does not implement freshest-item selection or fixture validation.
"""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.ids import sort_by_id
from chonoi.inputs import InputState
from chonoi.runner import Session

FRESHNESS = json.loads((Path(__file__).parent / "fixtures/p3_04_freshness.json").read_text(encoding="utf-8"))


def item(ident="I1", kind="ca_loc", fresh=100):
    return {"id": ident, "kind": kind, "fresh": fresh}


def order(ident="C1", table="T1", dish="ca_loc_nuong_trui", reserved=None):
    return {"id": ident, "table_id": table, "dish_id": dish, "order_tick": 0, "state": "waiting",
            "order_status": "reserved", "reserved": ["I1"] if reserved is None else reserved,
            "patience_ticks_left": 3600, "eat_ticks_left": 0, "base_price": 0, "tip": 0}


def session(stock=None, customers=None, replacements=None):
    s = Session("quan", load_contract()["tuning"], {"random_customers": False, "player": {"pos": [2, 8]}}, 42)
    q = s.sim
    q.stock = deepcopy([item()] if stock is None else stock)
    q.customers = deepcopy([order()] if customers is None else customers)
    q.freshness = dict(FRESHNESS)
    q.retry_calls = []
    advance = q._advance_kitchen_timers

    def scripted_p3_03(events):
        ready_events = []
        advance(ready_events)
        spoiled = set()
        decrement = Fraction(str(q.freshness["quan_decay_per_s"])) / q.tick_hz
        threshold = Fraction(str(q.freshness["spoiled_below"]))
        for obj in sort_by_id(q.stock):
            before = Fraction(str(obj["fresh"]))
            after = max(0, before - decrement)
            obj["fresh"] = float(after)
            if before >= threshold > after:
                spoiled.add(obj["id"])
                events.append(("spoiled", {"item_id": obj["id"], "kind": obj["kind"], "location": "stock"}))
        for c in sorted(sort_by_id(q.customers, key=lambda c: c["table_id"]), key=lambda c: c["order_tick"]):
            if c["order_status"] == "reserved" and spoiled.intersection(c["reserved"]):
                q.retry_calls.append(c["id"])
                c["reserved"] = list((replacements or {}).get(c["id"], []))
                c["order_status"] = "reserved" if c["reserved"] else "unfulfillable"
        events.extend(ready_events)

    q._advance_kitchen_timers = scripted_p3_03
    return s


def step(s, interact=False, pause=False):
    return s.step(InputState((0, 0), {}, {name for name, on in (("interact", interact), ("pause", pause)) if on}))
