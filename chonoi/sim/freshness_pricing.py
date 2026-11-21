"""P3-04 cooking transaction. P3-03 owns stock decay and reservation selection.

Call after decay/re-reservation, with physical stock objects and reserved IDs.
No schema conversion, item allocation, decay or re-reservation happens here.
"""

from collections import Counter
from copy import deepcopy
from fractions import Fraction
from math import isfinite

from ..errors import BadInput
from ..ids import sort_by_id


def _number(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or isinstance(value, float) and not isfinite(value)):
        return None
    return Fraction(str(value))


def consume_fresh_order(stock, customers, customer, menu_entry, freshness):
    """Return (locked price, event items), or None without changing any state.

    On success remove only the customer's reserved physical items in place.
    The caller performs assigned/stove transitions and clears reserved to [].
    Config comes from the manifest's root freshness block, supplied by P3-03.
    """
    if not isinstance(freshness, dict):
        raise BadInput("P3-04 requires manifest freshness configuration from P3-03")
    initial = _number(freshness.get("initial"))
    threshold = _number(freshness.get("spoiled_below"))
    if initial is None or threshold is None or not 0 <= threshold <= initial or initial <= 0:
        raise BadInput("invalid freshness initial/spoiled_below")
    if not isinstance(stock, list) or customer.get("order_status") != "reserved":
        return None
    reserved = customer.get("reserved")
    if (not isinstance(reserved, list) or not reserved
            or any(not isinstance(i, str) or not i for i in reserved)
            or len(set(reserved)) != len(reserved)):
        return None
    selected_ids = set(reserved)
    # Defend against inconsistent future P3-03 mutations; never steal a claim.
    for other in customers:
        if other is customer:
            continue
        claims = other.get("reserved")
        if not isinstance(claims, list) or any(not isinstance(i, str) for i in claims):
            return None
        if selected_ids.intersection(claims):
            return None
    physical = {}
    for item in stock:
        if (not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}
                or not isinstance(item["id"], str) or not item["id"] or item["id"] in physical):
            return None
        physical[item["id"]] = item
    if not selected_ids <= physical.keys():
        return None
    items = [physical[i] for i in reserved]
    recipe = menu_entry.get("recipe")
    price = menu_entry.get("price")
    if (not isinstance(recipe, dict) or not recipe
            or any(type(n) is not int or n <= 0 for n in recipe.values())
            or type(price) is not int or price <= 0
            or any(not isinstance(i["kind"], str) for i in items)
            or Counter(i["kind"] for i in items) != recipe):
        return None
    fresh = [_number(i["fresh"]) for i in items]
    if any(f is None or not threshold <= f <= initial for f in fresh):
        return None
    # Rational arithmetic avoids intermediate mean/float rounding before floor.
    scaled = price * sum(fresh) / (len(items) * initial)
    base_price = scaled.numerator // scaled.denominator
    event_items = sorted(sort_by_id(deepcopy(items)), key=lambda i: i["kind"])
    stock[:] = [i for i in stock if i["id"] not in selected_ids]
    return base_price, event_items
