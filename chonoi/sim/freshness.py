"""Độ tươi trong giỏ theo ADR-0001; không đọc/ghi file kho.

Đơn vị chính xác: 1 điểm = 240 units. Adapter kho bàn giao mảng cá thể
{id, kind, fresh}; sim giữ units cho tới khi xuất snapshot/event/handoff.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from ..ids import sort_by_id

UNITS_PER_POINT = 240


def units(points):
    return int((Decimal(str(points)) * UNITS_PER_POINT).to_integral_value(rounding=ROUND_HALF_UP))


def initialize(items, ids):
    hold = []
    for item in items:
        ids.reserve(item["id"])
        hold.append({"id": item["id"], "kind": item["kind"], "fresh_units": units(item["fresh"])})
    return hold


def export(items):
    return [{"id": item["id"], "kind": item["kind"],
             "fresh": item["fresh_units"] / UNITS_PER_POINT} for item in items]


def receive(sim, kind, amount):
    if sim.freshness is None:
        sim.hold.extend([kind] * amount)
        return {}
    items = [{"id": sim.ids.new("I"), "kind": kind,
              "fresh_units": units(sim.freshness["initial"])} for _ in range(amount)]
    sim.hold.extend(items)
    return {"item_ids": [item["id"] for item in items]}


def advance(hold, config, tick_hz, events):
    # The prescribed 0.5/s at 60 Hz is exactly 2 units per tick.
    decay = Fraction(str(config["gather_decay_per_s"])) * UNITS_PER_POINT / Fraction(str(tick_hz))
    threshold = units(config["spoiled_below"])
    for item in sort_by_id(hold):
        before = item["fresh_units"]
        total = item.get("decay_remainder", 0) + decay
        whole = int(total)
        item["decay_remainder"] = total - whole
        item["fresh_units"] = max(0, before - whole)
        if before >= threshold > item["fresh_units"]:
            events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "hold"}))
