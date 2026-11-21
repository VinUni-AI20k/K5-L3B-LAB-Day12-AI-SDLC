"""Lát 2: hái và bắt cá; GatherSim giữ thứ tự tick và ưu tiên cập bến.

Ticket: docs/tickets/phase-1/03-gather-actions.md.
Q1: giỏ không đủ chỗ thì giữ đàn và không đặt hồi chiêu mới.
"""

import math

from ..ids import sort_by_id
from .freshness import receive


def _nearest(entities, pos, radius):
    """Khoảng cách thật, gồm mép bán kính; hòa thì theo thứ tự id."""
    target = min(sort_by_id(entities), key=lambda e: math.dist(pos, e["pos"]), default=None)
    if target is not None and math.dist(pos, target["pos"]) <= radius:
        return target
    return None


def handle_gather_node(sim, events):
    """Hái một nút ready ở mặt nước, giữ nguyên nút nếu giỏ thiếu chỗ."""
    if not sim._at_surface():
        return
    target = _nearest((n for n in sim.nodes if n["regrow_ticks"] == 0),
                      sim.pos, sim.t["interact_radius"])
    if target is None:
        return
    amount = sim.t["node_yield"]
    free = sim.t["hold_capacity"] - len(sim.hold)
    if free < amount:
        events.append(("hold_full", {"action": "gather", "node_id": target["id"],
                                    "required": amount, "free": free}))
        return
    received = receive(sim, target["kind"], amount)
    target["regrow_ticks"] = int(round(sim.t["regrow_s"] * sim.tick_hz))
    events.append(("gather", {"node_id": target["id"], "kind": target["kind"], "amount": amount, **received}))


def handle_catch_fish(sim, events):
    """Bắt trọn đàn gần nhất khi lặn và hết hồi chiêu; không thử đàn khác."""
    if sim._at_surface() or sim.catch_cd_ticks > 0:
        return
    eligible = [f for f in sim.fish if f.get("age_ticks", 1) > 0]
    level = sim.active_upgrades.get("net", 0) if "net" in sim.extensions else 0
    if level:
        upgrade = next(u for u in sim.shop_upgrades["net"] if u["level"] == level)
        targets = [f for f in sort_by_id(eligible) if math.dist(sim.pos, f["pos"]) <= upgrade["radius"]]
        limit = upgrade["max_schools"]
    else:
        target = _nearest(eligible, sim.pos, sim.t["catch_radius"])
        targets = [target] if target is not None else []
        limit = 1
    caught = 0
    for target in targets:
        amount = sim.t["fish_yield"][target["kind"]]
        free = sim.t["hold_capacity"] - len(sim.hold)
        if free < amount:
            events.append(("hold_full", {"action": "catch", "fish_id": target["id"],
                                        "required": amount, "free": free}))
            continue
        received = receive(sim, target["kind"], amount)
        sim.fish.remove(target)
        events.append(("fish_caught", {"fish_id": target["id"], "kind": target["kind"],
                                       "yield": amount, **received}))
        caught += 1
        if caught == limit:
            break
    if caught:
        sim.catch_cd_ticks = int(round(sim.t["catch_cooldown_s"] * sim.tick_hz))
