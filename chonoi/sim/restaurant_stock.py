"""Cá thể trong kho quán và phần giữ chỗ của các đơn v1.2."""

from collections import Counter
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_individual_items


class RestaurantStock:
    def __init__(self, items, freshness, tick_hz):
        self.items = sort_by_id(validate_individual_items(items))
        for item in self.items:
            item["fresh"] = Fraction(str(item["fresh"]))
        self.per_tick = Fraction(str(freshness["quan_decay_per_s"])) / tick_hz
        self.minimum = Fraction(str(freshness["spoiled_below"]))
        self.freshness_scale = Fraction(str(freshness["initial"]))

    @staticmethod
    def _external(item):
        return {**item, "fresh": float(item["fresh"])}

    def snapshot(self):
        return [self._external(item) for item in self.items]

    def age(self):
        """Return only items crossing the threshold on this step, in ID order."""
        spoiled = []
        for item in self.items:
            before = item["fresh"]
            item["fresh"] = max(Fraction(0), before - self.per_tick)
            if before >= self.minimum > item["fresh"]:
                spoiled.append(item)
        return spoiled

    def reserve(self, recipe, blocked):
        available = sorted((item for item in self.items if item["id"] not in blocked
                            and item["fresh"] >= self.minimum),
                           key=lambda item: (-item["fresh"], id_key(item["id"])))
        claim = []
        for kind, count in sorted(recipe.items()):
            ids = [item["id"] for item in available if item["kind"] == kind][:count]
            if len(ids) != count:
                return None
            claim.extend(ids)
        return claim

    def _claim_items(self, recipe, claim, blocked):
        if (not isinstance(claim, list) or any(not isinstance(item_id, str) for item_id in claim)
                or len(set(claim)) != len(claim) or blocked.intersection(claim)):
            return None
        by_id = {item["id"]: item for item in self.items}
        items = [by_id.get(item_id) for item_id in claim]
        if (any(item is None or item["fresh"] < self.minimum for item in items)
                or Counter(item["kind"] for item in items) != recipe):
            return None
        return items

    def load_claims(self, ordered_customers, menu):
        """Respect explicit claims first, then fill missing claims in order."""
        claimed = set()
        to_reserve = []
        for customer in ordered_customers:
            if customer["order_status"] != "reserved":
                if customer.setdefault("reserved", []) != []:
                    raise BadInput("chỉ đơn reserved được giữ cá thể")
                continue
            recipe = menu[customer["dish_id"]]["recipe"]
            if "reserved" not in customer:
                to_reserve.append((customer, recipe))
                continue
            claim = customer["reserved"]
            if self._claim_items(recipe, claim, claimed) is None:
                raise BadInput(f"customers.{customer['id']}: reserved trùng, ươn hoặc sai công thức")
            claimed.update(claim)
        for customer, recipe in to_reserve:
            claim = self.reserve(recipe, claimed)
            if claim is None:
                raise BadInput(f"customers.{customer['id']}: không đủ cá thể để giữ theo công thức")
            customer["reserved"] = claim
            claimed.update(claim)

    def consume(self, recipe, claim, blocked, price):
        """Check and consume the exact held IDs, returning the price and event items."""
        items = self._claim_items(recipe, claim, blocked)
        if not items:
            return None
        base_price = price * sum(item["fresh"] for item in items) // (len(items) * self.freshness_scale)
        consumed = set(claim)
        self.items[:] = [item for item in self.items if item["id"] not in consumed]
        items.sort(key=lambda item: (item["kind"], id_key(item["id"])))
        return base_price, [self._external(item) for item in items]
