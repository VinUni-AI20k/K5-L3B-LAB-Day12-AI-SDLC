"""Kho quán theo cá thể cho contract v1.2."""

from collections import Counter
from fractions import Fraction
import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import KINDS


class FreshStock:
    def __init__(self, items, config, tick_hz):
        self.items = {}
        self.threshold = Fraction(str(config["spoiled_below"]))
        self.decay = Fraction(str(config["quan_decay_per_s"])) / tick_hz
        for item in items:
            if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
                raise BadInput("invalid inventory item")
            ident, kind, fresh = item["id"], item["kind"], item["fresh"]
            if (not isinstance(ident, str) or not ident or ident in self.items
                    or kind not in KINDS or type(fresh) not in (int, float)
                    or not 0 <= fresh <= 100 or not math.isfinite(fresh)):
                raise BadInput("invalid or duplicate inventory item")
            self.items[ident] = dict(item, fresh=Fraction(str(fresh)))

    @staticmethod
    def _output(item):
        return dict(item, fresh=float(item["fresh"]))

    def snapshot(self):
        return [self._output(item) for item in sort_by_id(self.items.values())]

    def advance(self, events):
        spoiled = set()
        for item in sort_by_id(self.items.values()):
            previous = item["fresh"]
            item["fresh"] = max(Fraction(0), previous - self.decay)
            if previous >= self.threshold > item["fresh"]:
                spoiled.add(item["id"])
                events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "stock"}))
        return spoiled

    def reserve(self, recipe, held):
        candidates = sorted(self.items.values(), key=lambda item: (-item["fresh"], id_key(item["id"])))
        ids = []
        for kind, quantity in recipe.items():
            choices = [item["id"] for item in candidates if item["kind"] == kind
                       and item["id"] not in held and item["fresh"] >= self.threshold]
            if len(choices) < quantity:
                return None
            ids.extend(choices[:quantity])
        return ids

    def validate_reservation(self, ids, recipe, held):
        if (not isinstance(ids, list) or any(not isinstance(ident, str) for ident in ids)
                or len(ids) != len(set(ids))):
            raise BadInput("reserved must list unique inventory ids")
        for ident in ids:
            if ident in held or ident not in self.items or self.items[ident]["fresh"] < self.threshold:
                raise BadInput("reserved item unavailable")
        if Counter(self.items[ident]["kind"] for ident in ids) != recipe:
            raise BadInput("reserved items do not match recipe")

    def consume(self, ids, list_price):
        items = [self.items.pop(ident) for ident in ids]
        average = sum(item["fresh"] for item in items) / len(items)
        price = math.floor(list_price * average / 100)
        items.sort(key=lambda item: (item["kind"], id_key(item["id"])))
        return [self._output(item) for item in items], price
