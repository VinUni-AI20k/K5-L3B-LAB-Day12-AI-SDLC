"""Freshness shared by all simulations; integer units avoid boundary drift."""
from .ids import sort_by_id

UNITS = 240


def to_units(fresh: float) -> int:
    return round(fresh * UNITS)


def to_fresh(u: int) -> float:
    return u / UNITS


def item_out(it):
    return {"id": it["id"], "kind": it["kind"], "fresh": round(to_fresh(it["fresh_u"]), 6)}


def is_spoiled(u, tuning) -> bool:
    return u < to_units(tuning["freshness"]["spoiled_below"])


def decay_per_tick_u(tuning, where):
    if where not in {"gather", "quan"}:
        raise ValueError(f"unknown freshness location: {where}")
    return round(tuning["freshness"][f"{where}_decay_per_s"] * UNITS / tuning["tick_hz"])


def freshest_first(items):
    # Stable second sort preserves the shared numeric id order for ties.
    return sorted(sort_by_id(items), key=lambda it: -it["fresh_u"])
