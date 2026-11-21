"""P3-04 integration fixture using the real P3-03 stock engine after merge.

Only observes retry calls; does not replace decay, selection or cooking.
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
    s = Session("quan", load_contract()["tuning"], {
        "random_customers": False, "player": {"pos": [2, 8]},
        "stock": deepcopy([item()] if stock is None else stock),
        "customers": deepcopy([order()] if customers is None else customers)}, 42)
    q = s.sim
    q.freshness = dict(FRESHNESS)
    q.retry_calls = []
    age_stock = q._age_stock

    def scripted_p3_03(events):
        affected = []
        decrement = Fraction(str(q.freshness["quan_decay_per_s"])) / q.tick_hz
        threshold = Fraction(str(q.freshness["spoiled_below"]))
        spoiled = {i["id"] for i in q.stock if i["fresh"] >= threshold > i["fresh"] - decrement}
        for c in sorted(sort_by_id(q.customers, key=lambda c: c["table_id"]), key=lambda c: c["order_tick"]):
            if c["order_status"] == "reserved" and spoiled.intersection(c["reserved"]):
                affected.append(c)
        age_stock(events)
        for c in affected:
            q.retry_calls.append(c["id"])
            if replacements and c["id"] in replacements:
                assert c["reserved"] == replacements[c["id"]]

    q._age_stock = scripted_p3_03
    return s


def step(s, interact=False, pause=False):
    return s.step(InputState((0, 0), {}, {name for name, on in (("interact", interact), ("pause", pause)) if on}))
